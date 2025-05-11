import streamlit as st
st.set_page_config(page_title="🧑‍🍳Chef Tai🛠️", layout="centered")

st.markdown("""
<style>
/* Selectively force black text for headings and body text */
[data-testid="stAppViewContainer"] h1,
[data-testid="stAppViewContainer"] h2,
[data-testid="stAppViewContainer"] h3,
[data-testid="stAppViewContainer"] p,
[data-testid="stAppViewContainer"] li {
color: #000 !important;
}

/* Mobile-specific font-size adjustments */
@media (max-width: 600px) {
  [data-testid="stAppViewContainer"] h1 {
    font-size: 2rem !important;
  }
  [data-testid="stAppViewContainer"] h2,
  [data-testid="stAppViewContainer"] h3 {
    font-size: 1.2rem !important;
  }
}

/* Adjust column widths in Sequence table */
table[data-testid="stTable"] td:nth-child(1) { /* Step */
    min-width: 150px !important;
    max-width: 150px !important;
    word-break: normal;
}
table[data-testid="stTable"] td:nth-child(2) { /* Part */
    min-width: 50px !important;
    max-width: 50px !important;
    word-break: normal;
}
table[data-testid="stTable"] td:nth-child(3) { /* Instruction */
    min-width: 300px !important;
    word-break: normal;
}
table[data-testid="stTable"] td:nth-child(4) { /* CycleTime */
    min-width: 80px !important;
    max-width: 80px !important;
    word-break: normal;
}
table[data-testid="stTable"] td:nth-child(5) { /* Parallel */
    min-width: 60px !important;
    max-width: 60px !important;
    word-break: normal;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""<style>
[data-testid="stAppViewContainer"] {
    background-color: #d8d4c0;
}

/* Global heading size adjustments */
h1 {
    font-size: 2rem !important;
}
h3 {
    font-size: 1rem !important;
}
</style>""", unsafe_allow_html=True)

from pathlib import Path
header_path = Path(__file__).parent / 'chef_tai_header_centered.png'
if header_path.exists():
    st.image(str(header_path), use_container_width=True)

import pandas as pd
import requests
from io import BytesIO
from PIL import Image
import re

def format_quantity(val):
    return str(int(val)) if float(val).is_integer() else f"{val:.1f}"

@st.cache_data
def load_data():
    df = pd.read_excel("Recipe_Database_Corrected.xlsx", sheet_name=None)
    ingredients = df["Ingredients"]
    recipes = df["Recipes"]
    components = df["Components"]
    ingredient_dict = df["IngredientDict"]
    steps = df["Steps"]
    tools = df.get("Tools", pd.DataFrame(columns=["RecipeID", "ToolName", "ToolName_zh", "Optional"]))  # Load Tools with Optional column
    merged = (
        ingredients
        .merge(components.drop(columns=["RecipeID"]), on="ComponentID", how="left")
        .merge(recipes, on="RecipeID", how="left")
        .merge(ingredient_dict, on="Ingredient", how="left")
    )
    return merged, recipes, steps, tools

df, recipes_df, steps_df, tools_df = load_data()
lang = st.radio("選擇語言 / Choose Language", ["中文", "English"])
st.title("🧑‍🍳🛠️ 食譜組裝器" if lang == "中文" else "🧑‍🍳🛠️ Taste Fabrication")

# Session state for filter management
if 'selected_category' not in st.session_state:
    st.session_state.selected_category = 'All'
if 'selected_subcategory' not in st.session_state:
    st.session_state.selected_subcategory = 'All'

# Category & Style Filters
category_display = "類別 (選用)" if lang == "中文" else "Category(Optional)"
style_display = "風格(選用)" if lang == "中文" else "Style(Optional)"
category_options = ['All'] + sorted(recipes_df['Category_zh' if lang == "中文" else 'Category'].dropna().unique())
style_options = ['All'] + sorted(recipes_df['SubCategory_zh' if lang == "中文" else 'SubCategory'].dropna().unique())

# Display filters with session state
selected_category = st.selectbox(category_display, category_options, index=category_options.index(st.session_state.selected_category))
if selected_category != 'All':
    category_key = 'Category_zh' if lang == "中文" else 'Category'
    filtered_recipes = recipes_df[recipes_df[category_key] == selected_category]
    available_styles = ['All'] + sorted(filtered_recipes['SubCategory_zh' if lang == "中文" else 'SubCategory'].dropna().unique())
    selected_subcategory = st.selectbox(style_display, available_styles, index=available_styles.index(st.session_state.selected_subcategory) if st.session_state.selected_subcategory in available_styles else 0)
else:
    selected_subcategory = st.selectbox(style_display, style_options, index=style_options.index(st.session_state.selected_subcategory))

# Update session state with current selections
st.session_state.selected_category = selected_category
st.session_state.selected_subcategory = selected_subcategory

# Clear Filters button
if st.button("清除篩選" if lang == "中文" else "Clear Filters"):
    st.session_state.selected_category = 'All'
    st.session_state.selected_subcategory = 'All'
    st.rerun()

filtered_df = df.copy()
if selected_category != 'All':
    category_key = 'Category_zh' if lang == "中文" else 'Category'
    filtered_df = filtered_df[filtered_df[category_key] == selected_category]
if selected_subcategory != 'All':
    subcategory_key = 'SubCategory_zh' if lang == "中文" else 'SubCategory'
    filtered_df = filtered_df[filtered_df[subcategory_key] == selected_subcategory]

filtered_df["RecipeDisplay"] = filtered_df["RecipeName_zh"] if lang == "中文" else filtered_df["RecipeName"]
recipe_options = filtered_df["RecipeDisplay"].unique()
if len(recipe_options) > 0:
    selected = st.multiselect("請選擇食譜" if lang == "中文" else "Select Recipe", recipe_options)
else:
    selected = []
    st.info("目前篩選條件下無可用食譜" if lang == "中文" else "No recipes available under current filters.")

if selected:
    multipliers = {}
    for recipe in selected:
        multipliers[recipe] = st.slider(f"{recipe} - {'份量倍率' if lang == '中文' else 'Multiplier'}", 1, 10, 1, key=recipe)

    selected_ids = filtered_df[filtered_df["RecipeDisplay"].isin(selected)]["RecipeID"].unique()

    for recipe in selected:
        rec_df = filtered_df[filtered_df["RecipeDisplay"] == recipe].copy()
        recipe_id = rec_df["RecipeID"].iloc[0]
        mult = multipliers[recipe]

        # Handle image URL and extraction
        image_url = rec_df["ImageURL"].iloc[0]
        if isinstance(image_url, str) and image_url.startswith("http"):
            display_url = image_url
            if "/a/" in image_url or "/gallery/" in image_url:
                try:
                    html = requests.get(image_url).text
                    m = re.search(r'<meta property="og:image" content="([^"]+)"', html)
                    if m:
                        display_url = m.group(1)
                    else:
                        m2 = re.search(r'<link rel="image_src" href="([^"]+)"', html)
                        if m2:
                            display_url = m2.group(1)
                except:
                    pass
            try:
                resp = requests.get(display_url)
                img = Image.open(BytesIO(resp.content))
                img = img.resize((350, 250))
                st.image(img)
            except:
                st.markdown(f'<img src="{display_url}" width="350">', unsafe_allow_html=True)

        # Recipe info display
        info = rec_df.iloc[0][["Portion", "Method"]]
        portion = f"{info['Portion']} x{mult}"
        # Calculate total time for this recipe (excluding parallel steps)
        recipe_steps = steps_df[steps_df["RecipeID"] == recipe_id]
        total_recipe_time = recipe_steps[recipe_steps["Parallel"] == False]["CycleTime"].sum() if 'Parallel' in recipe_steps.columns and 'CycleTime' in recipe_steps.columns else 0
        if lang == "中文":
            st.markdown(f"### 🍽️ {recipe} — 👥 分量：{portion}")
            st.markdown(f"🍳 做法：{info['Method']}")
            st.markdown(f"⏱️ 預估時間：{total_recipe_time} 分鐘")
        else:
            st.markdown(f"### 🍽️ {recipe} — 👥 Portion: {portion}")
            st.markdown(f"🍳 Method: {info['Method']}")
            st.markdown(f"⏱️ Estimated Time: {total_recipe_time} min")


        # Display Tool Collection Bag
        st.subheader("🧰 工具收集袋" if lang == "中文" else "🧰 Tool Collection Bag")
        recipe_tools = tools_df[tools_df["RecipeID"] == recipe_id]
        if recipe_tools.empty:
            st.info("工具資料待補" if lang == "中文" else "Tool data to be added")
        else:
            if lang == "中文":
                tool_display = recipe_tools[["ToolName_zh", "Optional"]]
                tool_display.columns = ["工具", "選用"]
                tool_display["選用"] = tool_display["選用"].apply(lambda x: "✓" if x in ["✓", "V"] else "")
            else:
                tool_display = recipe_tools[["ToolName", "Optional"]]
                tool_display.columns = ["Tool", "Optional"]
                tool_display["Optional"] = tool_display["Optional"].apply(lambda x: "(optional)" if x in ["✓", "V"] else "")
            st.table(tool_display.reset_index(drop=True))

        # Components title and table display
        st.subheader("🫜 BoM物料表" if lang == "中文" else "🫜 BoM (Bill of Materials)")
        for comp in rec_df["ComponentName"].unique():
            comp_df = rec_df[rec_df["ComponentName"] == comp]
            comp_display = comp_df["ComponentName_zh"].iloc[0] if lang == "中文" else comp
            if lang == "中文":
                comp_df["食材"] = comp_df["Ingredient_zh"]
                display = (
                    comp_df.groupby(["食材", "Unit", "Optional"])["Amount"]
                    .sum().mul(mult).reset_index()
                )
                display["數量"] = display["Amount"].apply(format_quantity)
                display["選用"] = display["Optional"].apply(lambda x: "✓" if x else "")
                display = display[["食材", "數量", "Unit", "選用"]]
                display.columns = ["食材", "數量", "單位", "選用"]
            else:
                display = (
                    comp_df.groupby(["Ingredient", "Unit", "Optional"])["Amount"]
                    .sum().mul(mult).reset_index()
                )
                display["Quantity"] = display["Amount"].apply(format_quantity)
                display["Optional"] = display["Optional"].apply(lambda x: "✓" if x else "")
                display = display[["Ingredient", "Quantity", "Unit", "Optional"]]

            st.subheader(f"• {comp_display}")
            st.table(display.reset_index(drop=True))

        # Display Recipe Sequence with merged Parts
        st.subheader("📋 生產流程" if lang == "中文" else "📋 Sequence")
        step_data = steps_df[steps_df["RecipeID"] == recipe_id]
        
        # Check if step_data is empty or missing required columns
        required_columns = ["StepOrder", "Part_zh" if lang == "中文" else "Part", "Instruction_zh" if lang == "中文" else "Instruction_en"]
        if step_data.empty or not all(col in step_data.columns for col in required_columns):
            st.info("步驟資料待補" if lang == "中文" else "Step data to be added")
        else:
            step_data = step_data[required_columns + (["CycleTime", "Parallel"] if "CycleTime" in step_data.columns and "Parallel" in step_data.columns else [])]
            step_data = step_data.rename(columns={
                "StepOrder": "步驟" if lang == "中文" else "Step",
                "Part_zh": "部位" if lang == "中文" else "Part",
                "Part": "Part",
                "Instruction_zh": "說明" if lang == "中文" else "Instruction",
                "Instruction_en": "Instruction",
                "CycleTime": "時間" if lang == "中文" else "CycleTime",
                "Parallel": "並行" if lang == "中文" else "Parallel"
            })
            
            # Adjust Part to show only on first occurrence
            sequence_data = []
            last_part = None
            for index, row in step_data.iterrows():
                current_part = row["部位" if lang == "中文" else "Part"]
                if current_part != last_part:
                    sequence_data.append(row)
                    last_part = current_part
                else:
                    new_row = row.copy()
                    new_row["部位" if lang == "中文" else "Part"] = ""  # Empty Part for subsequent rows
                    sequence_data.append(new_row)
            
            sequence_df = pd.DataFrame(sequence_data)
            # Only apply Parallel transformation if the column exists
            if "並行" in sequence_df.columns if lang == "中文" else "Parallel" in sequence_df.columns:
                sequence_df["並行" if lang == "中文" else "Parallel"] = sequence_df["並行" if lang == "中文" else "Parallel"].apply(lambda x: "✓" if x else "")
            st.table(sequence_df.reset_index(drop=True))

    # Shopping list with total estimated time and aggregated tools
    st.subheader("📝 採購清單" if lang == "中文" else "📝 Porcurement")
    all_df = filtered_df[filtered_df["RecipeDisplay"].isin(selected)].copy()
    all_df["Multiplier"] = all_df["RecipeDisplay"].map(multipliers)
    all_df["TotalAmount"] = all_df["Amount"] * all_df["Multiplier"]

    # Calculate total time for all selected recipes (excluding parallel steps)
    total_time = 0
    for recipe_id in selected_ids:
        recipe_steps = steps_df[steps_df["RecipeID"] == recipe_id]
        if 'Parallel' in recipe_steps.columns and 'CycleTime' in recipe_steps.columns:
            total_time += recipe_steps[recipe_steps["Parallel"] == False]["CycleTime"].sum()

    # Aggregate ingredients
    if lang == "中文":
        st.markdown(f"### ⏱️ 預估總時間：{total_time} 分鐘")
        all_df["食材"] = all_df["Ingredient_zh"]
        summary = all_df.groupby(["食材", "Unit", "Optional"])["TotalAmount"].sum().reset_index()
        summary["數量"] = summary["TotalAmount"].apply(format_quantity)
        summary["選用"] = summary["Optional"].apply(lambda x: "✓" if x else "")
        summary = summary[["食材", "數量", "Unit", "選用"]]
        summary.columns = ["食材", "數量", "單位", "選用"]
        lines = [f"{row['食材']}: {row['數量']}{row['單位']}" + (" (選用)" if row['選用'] else "") for _, row in summary.iterrows()]
    else:
        st.markdown(f"### ⏱️ Estimated Total Time: {total_time} min")
        summary = all_df.groupby(["Ingredient", "Unit", "Optional"])["TotalAmount"].sum().reset_index()
        summary["Quantity"] = summary["TotalAmount"].apply(format_quantity)
        summary["Optional"] = summary["Optional"].apply(lambda x: "✓" if x else "")
        summary = summary[["Ingredient", "Quantity", "Unit", "Optional"]]
        lines = [f"{row['Ingredient']}: {row['Quantity']}{row['Unit']}" + (" (optional)" if row['Optional'] else "") for _, row in summary.iterrows()]

    # Aggregate tools
    all_tools = tools_df[tools_df["RecipeID"].isin(selected_ids)].copy()
    if not all_tools.empty:
        if lang == "中文":
            tool_summary = all_tools.groupby(["ToolName_zh", "Optional"]).size().reset_index(name="Count")
            tool_summary["選用"] = tool_summary["Optional"].apply(lambda x: "✓" if x in ["✓", "V"] else "")
            tool_lines = [f"{row['ToolName_zh']}" + (" (選用)" if row['選用'] else "") for _, row in tool_summary.iterrows()]
        else:
            tool_summary = all_tools.groupby(["ToolName", "Optional"]).size().reset_index(name="Count")
            tool_summary["Optional"] = tool_summary["Optional"].apply(lambda x: "(optional)" if x in ["✓", "V"] else "")
            tool_lines = [f"{row['ToolName']}" + (" (optional)" if row['Optional'] else "") for _, row in tool_summary.iterrows()]
        lines.extend(tool_lines)

    st.code("\n".join(lines))
else:
    st.info("請選擇至少一道食譜" if lang == "中文" else "Please select at least one recipe.")