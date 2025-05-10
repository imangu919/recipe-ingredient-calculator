import streamlit as st
import pandas as pd
import requests
from io import BytesIO
from PIL import Image
import re

# --- 行動裝置友善 CSS ---
st.markdown("""<style>
[data-testid=\"stAppViewContainer\"] {
  padding-left: 0.5rem;
  padding-right: 0.5rem;
}
h1 { font-size: 1.8rem !important; }
h2 { font-size: 1.4rem !important; }
.css-1d391kg, .css-1bnpi1v p, .css-1bnpi1v li, .css-1bnpi1v code {
  font-size: 1rem !important;
}
.stSlider > div {
  width: 100% !important;
}
@media (max-width: 600px) {
  h1 { font-size: 1.6rem !important; }
  h2 { font-size: 1.2rem !important; }
  .css-1d391kg, .css-1bnpi1v p, .css-1bnpi1v li { font-size: 0.9rem !important; }
}
</style>
""", unsafe_allow_html=True)
# -------------------------------

def format_quantity(val):
    return str(int(val)) if float(val).is_integer() else f"{val:.1f}"

@st.cache_data
def load_data():
    df = pd.read_excel("Recipe_Database_Corrected.xlsx", sheet_name=None)
    ingredients = df["Ingredients"]
    recipes = df["Recipes"]
    components = df["Components"]
    ingredient_dict = df["IngredientDict"]
    merged = (
        ingredients
        .merge(components.drop(columns=["RecipeID"]), on="ComponentID", how="left")
        .merge(recipes, on="RecipeID", how="left")
        .merge(ingredient_dict, on="Ingredient", how="left")
    )
    return merged

df = load_data()
lang = st.radio("選擇語言 / Choose Language", ["中文", "English"])
st.title("🧑‍🍳 食譜材料計算工具" if lang == "中文" else "🧑‍🍳 Recipe Ingredient Calculator")

df["RecipeDisplay"] = df["RecipeName_zh"] if lang == "中文" else df["RecipeName"]
selected = st.multiselect("請選擇食譜" if lang == "中文" else "Select Recipe", df["RecipeDisplay"].unique())

if selected:
    multipliers = {recipe: st.slider(
        f"{recipe} - {'份量倍率' if lang=='中文' else 'Multiplier'}", 1, 10, 1, key=recipe
    ) for recipe in selected}

    for recipe in selected:
        rec_df = df[df["RecipeDisplay"] == recipe].copy()
        mult = multipliers[recipe]

        image_url = rec_df["ImageURL"].iloc[0]
        if isinstance(image_url, str) and image_url.startswith("http"):
            display_url = image_url
            if "/a/" in image_url or "/gallery/" in image_url:
                try:
                    html = requests.get(image_url).text
                    m = re.search(r'<meta property="og:image" content="([^\"]+)"', html)
                    if m: display_url = m.group(1)
                except: pass
            try:
                resp = requests.get(display_url)
                img = Image.open(BytesIO(resp.content))
                img = img.resize((350, 250))
                st.image(img)
            except:
                st.markdown(f'<img src="{display_url}" width="350">', unsafe_allow_html=True)

        info = rec_df.iloc[0][["Portion","Method","Temperature","Time"]]
        portion = f"{info['Portion']} x{mult}"
        if lang == "中文":
            st.markdown(f"### 🍽️ {recipe} — 👥 分量：{portion}")
            st.markdown(f"🍳 做法：{info['Method']}")
            st.markdown(f"🌡️ 溫度：{info['Temperature']}")
            st.markdown(f"⏱️ 時間：{info['Time']} 分鐘")
        else:
            st.markdown(f"### 🍽️ {recipe} — 👥 Portion: {portion}")
            st.markdown(f"🍳 Method: {info['Method']}")
            st.markdown(f"🌡️ Temp: {info['Temperature']}")
            st.markdown(f"⏱️ Time: {info['Time']} min")

        for comp in rec_df["ComponentName"].unique():
            comp_df = rec_df[rec_df["ComponentName"] == comp]
            comp_display = comp_df["ComponentName_zh"].iloc[0] if lang=="中文" else comp
            if lang=="中文":
                comp_df["食材"] = comp_df["Ingredient_zh"]
                display = comp_df.groupby(["食材","Unit","Optional"])["Amount"].sum().mul(mult).reset_index()
                display["數量"] = display["Amount"].apply(format_quantity)
                display["選用"] = display["Optional"].apply(lambda x: "✓" if x else "")
                display = display[["食材","數量","Unit","選用"]]
                display.columns = ["食材","數量","單位","選用"]
            else:
                display = comp_df.groupby(["Ingredient","Unit","Optional"])["Amount"].sum().mul(mult).reset_index()
                display["Quantity"] = display["Amount"].apply(format_quantity)
                display["Optional"] = display["Optional"].apply(lambda x: "✓" if x else "")
                display = display[["Ingredient","Quantity","Unit","Optional"]]
            st.subheader(f"• {comp_display}")
            st.table(display)

    st.subheader("📝 購物清單" if lang=="中文" else "📝 Shopping List")
    all_df = df[df["RecipeDisplay"].isin(selected)].copy()
    all_df["Multiplier"] = all_df["RecipeDisplay"].map(multipliers)
    all_df["TotalAmount"] = all_df["Amount"] * all_df["Multiplier"]
    if lang=="中文":
        all_df["食材"] = all_df["Ingredient_zh"]
        summary = all_df.groupby(["食材","Unit","Optional"])["TotalAmount"].sum().reset_index()
        summary["數量"] = summary["TotalAmount"].apply(format_quantity)
        summary["選用"] = summary["Optional"].apply(lambda x: "✓" if x else "")
        summary = summary[["食材","數量","Unit","選用"]]
        summary.columns = ["食材","數量","單位","選用"]
        lines = [f"{row['食材']}: {row['數量']}{row['單位']}"+ (" (選用)" if row['選用'] else "") for _, row in summary.iterrows()]
    else:
        summary = all_df.groupby(["Ingredient","Unit","Optional"])["TotalAmount"].sum().reset_index()
        summary["Quantity"] = summary["TotalAmount"].apply(format_quantity)
        summary["Optional"] = summary["Optional"].apply(lambda x: "✓" if x else "")
        summary = summary[["Ingredient","Quantity","Unit","Optional"]]
        lines = [f"{row['Ingredient']}: {row['Quantity']}{row['Unit']}"+ (" (optional)" if row['Optional'] else "") for _, row in summary.iterrows()]
    st.code("\n".join(lines))
else:
    st.info("請選擇至少一道食譜" if lang=="中文" else "Please select at least one recipe.")
