import streamlit as st
from pathlib import Path
import pandas as pd
import requests
from io import BytesIO
from PIL import Image
import re
import random
import json
from datetime import datetime

# Set page configuration
st.set_page_config(page_title="🧑‍🍳Chef Tai🛠️", layout="centered")

# Custom CSS and JavaScript
st.markdown("""
<style>
/* Ensure button text is visible in dark mode */
@media (prefers-color-scheme: dark) {
    [data-testid="stButton"] button {
        color: #fff !important;
    }
    [data-testid="stButton"] button p {
        color: #fff !important;
    }
    /* Adjust number input label and input text color in dark mode */
    [data-testid="stNumberInput"] label,
    [data-testid="stNumberInput"] input,
    [data-testid="stNumberInput"] > div > div > input,
    [data-testid="stNumberInput"] > div > label,
    [data-testid="stNumberInput"] .stNumberInput input {
        color: #fff !important;
    }
    /* Adjust input box background in dark mode */
    [data-testid="stNumberInput"] input,
    [data-testid="stNumberInput"] > div > div > input,
    [data-testid="stNumberInput"] .stNumberInput input {
        background-color: #444 !important;
        border: 1px solid #666 !important;
    }
    /* Adjust slider values text color in dark mode */
    [data-testid="stSlider"] .stSliderValue {
        color: #fff !important;
    }
}

/* Force black text for content elements, exclude interactive widgets */
[data-testid="stAppViewContainer"] {
    background-color: #d8d4c0 !important;
}

/* Apply black text to content elements only */
[data-testid="stAppViewContainer"] h1,
[data-testid="stAppViewContainer"] h2,
[data-testid="stAppViewContainer"] h3,
[data-testid="stAppViewContainer"] p,
[data-testid="stAppViewContainer"] li,
[data-testid="stAppViewContainer"] td,
[data-testid="stAppViewContainer"] th,
[data-testid="stAppViewContainer"] div.stMarkdown,
[data-testid="stAppViewContainer"] div.stInfo,
[data-testid="stAppViewContainer"] div.stCodeBlock {
    color: #000 !important;
}

/* Force black text for slider values in light mode */
[data-testid="stSlider"] .stSliderValue {
    color: #000 !important;
}

/* Force black text for number input labels and values in light mode */
[data-testid="stNumberInput"] label,
[data-testid="stNumberInput"] input {
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
<script>
if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
    const inputs = document.querySelectorAll('[data-testid="stNumberInput"] input');
    inputs.forEach(input => {
        input.style.color = '#fff';
        input.style.backgroundColor = '#444';
        input.style.border = '1px solid #666';
    });
}
</script>
""", unsafe_allow_html=True)

# Load header image
header_path = Path(__file__).parent / 'chef_tai_header_centered.png'
if header_path.exists():
    st.image(str(header_path), use_container_width=True)

# Suggestion for light mode before language selection
st.markdown("💡 建議使用淺色模式以獲得最佳體驗 / Suggest using light mode for the best experience")

# Language selection
lang = st.radio("選擇語言 / Choose Language", ["中文", "English"])

# Visit counter logic with date tracking
visit_file = Path(__file__).parent / 'visit_history.json'
current_date = datetime.now().strftime("%Y-%m-%d")  # e.g., "2025-06-03"

# Initialize or load visit history
if visit_file.exists():
    with open(visit_file, 'r') as f:
        visit_data = json.load(f)
else:
    visit_data = {"visits": []}

# Add current visit with timestamp
current_timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
visit_data["visits"].append({"timestamp": current_timestamp})

# Save updated visit history
with open(visit_file, 'w') as f:
    json.dump(visit_data, f, indent=4)

# Calculate total and today's visits
total_visits = len(visit_data["visits"])
today_visits = sum(1 for visit in visit_data["visits"] if visit["timestamp"].startswith(current_date))

# Display visit counts
if lang == "中文":
    st.markdown(f"**今日訪客數：{today_visits} | 歷史總訪客數：{total_visits}**")
else:
    st.markdown(f"**Today's Visits: {today_visits} | Total Visits: {total_visits}**")

# Title after language selection
st.title("🧑‍🍳🛠️ 食譜組裝器" if lang == "中文" else "🧑‍🍳🛠️ Flavor Engine")

# Utility function for formatting quantities
def format_quantity(val):
    return str(int(val)) if float(val).is_integer() else f"{val:.1f}"

# Function to resize image while maintaining aspect ratio
def resize_image_with_aspect_ratio(image, max_width=500, max_height=700):  # Increased dimensions
    img_width, img_height = image.size
    aspect_ratio = img_width / img_height

    # Calculate new dimensions while maintaining aspect ratio
    if img_width > max_width:
        new_width = max_width
        new_height = int(max_width / aspect_ratio)
    else:
        new_width = img_width
        new_height = img_height

    if new_height > max_height:
        new_height = max_height
        new_width = int(max_height * aspect_ratio)

    return image.resize((new_width, new_height), Image.Resampling.LANCZOS)

# Load data
@st.cache_data
def load_data():
    df = pd.read_excel("Recipe_Database_Corrected.xlsx", sheet_name=None)
    ingredients = df["Ingredients"]
    recipes = df["Recipes"]
    components = df["Components"]
    ingredient_dict = df["IngredientDict"]
    steps = df["Steps"]
    tools = df.get("Tools", pd.DataFrame(columns=["RecipeID", "ToolName", "ToolName_zh", "Optional"]))
    merged = (
        ingredients
        .merge(components.drop(columns=["RecipeID"]), on="ComponentID", how="left")
        .merge(recipes, on="RecipeID", how="left")
        .merge(ingredient_dict, on="Ingredient", how="left")
    )
    return merged, recipes, steps, tools

df, recipes_df, steps_df, tools_df = load_data()

# Session state for filter management
if 'selected_category' not in st.session_state:
    st.session_state.selected_category = 'All'
if 'selected_subcategory' not in st.session_state:
    st.session_state.selected_subcategory = 'All'

# Chef Tai's Surprise Pick Section (精細挑選)
with st.expander("🎉 Chef Tai的驚喜挑選" if lang == "中文" else "🎉 Chef Tai's Surprise Pick", expanded=False):
    mode = st.radio("選擇模式" if lang == "中文" else "Select Mode", ["基本模式", "進階模式"] if lang == "中文" else ["Basic Mode", "Advanced Mode"])
    if 'selected' not in st.session_state:
        st.session_state.selected = []
    filtered_df = df.copy()
    if st.session_state.selected_category != 'All':
        category_key = 'Category_zh' if lang == "中文" else 'Category'
        filtered_df = filtered_df[filtered_df[category_key] == st.session_state.selected_category]
    if st.session_state.selected_subcategory != 'All':
        subcategory_key = 'SubCategory_zh' if lang == "中文" else 'SubCategory'
        filtered_df = filtered_df[filtered_df[subcategory_key] == st.session_state.selected_subcategory]
    filtered_df["RecipeDisplay"] = filtered_df["RecipeName_zh"] if lang == "中文" else filtered_df["RecipeName"]
    recipe_options = filtered_df["RecipeDisplay"].unique()
    if mode == ("基本模式" if lang == "中文" else "Basic Mode"):
        num_dishes = st.number_input("選擇隨機餐點數量" if lang == "中文" else "Number of Dishes to Randomize", min_value=1, max_value=5, value=1)
        if st.button("隨機挑選" if lang == "中文" else "Random Pick"):
            available_recipes = list(recipe_options)
            if len(available_recipes) == 0:
                st.error("目前篩選條件下無可用食譜" if lang == "中文" else "No recipes available under current filters.")
            else:
                num_to_select = min(num_dishes, len(available_recipes))
                selected_recipes = random.sample(available_recipes, num_to_select)
                st.session_state.selected = selected_recipes
                st.success(f"已隨機挑選 {num_to_select} 道餐點！" if lang == "中文" else f"Randomly selected {num_to_select} dishes!")
    else:
        num_dishes = st.number_input("選擇隨機餐點數量" if lang == "中文" else "Number of Dishes to Randomize", min_value=1, max_value=5, value=1)
        filters = []
        for i in range(num_dishes):
            st.markdown(f"**第 {i+1} 道餐點設定**" if lang == "中文" else f"**Dish {i+1} Settings**")
            cat = st.selectbox(
                f"類別 (第 {i+1} 道)" if lang == "中文" else f"Category (Dish {i+1})",
                ['All'] + sorted(recipes_df['Category_zh' if lang == "中文" else 'Category'].dropna().unique()),
                key=f"adv_category_{i}"
            )
            if cat != 'All':
                category_key = 'Category_zh' if lang == "中文" else 'Category'
                filtered_for_style = recipes_df[recipes_df[category_key] == cat]
                available_styles = ['All'] + sorted(filtered_for_style['SubCategory_zh' if lang == "中文" else 'SubCategory'].dropna().unique())
            else:
                available_styles = ['All'] + sorted(recipes_df['SubCategory_zh' if lang == "中文" else 'SubCategory'].dropna().unique())
            subcat = st.selectbox(
                f"風格 (第 {i+1} 道)" if lang == "中文" else f"Style (Dish {i+1})",
                available_styles,
                key=f"adv_subcategory_{i}"
            )
            filters.append((cat, subcat))
        if st.button("隨機挑選" if lang == "中文" else "Random Pick"):
            selected_recipes = []
            used_recipes = set()
            for cat, subcat in filters:
                temp_df = filtered_df.copy()
                if cat != 'All':
                    category_key = 'Category_zh' if lang == "中文" else 'Category'
                    temp_df = temp_df[temp_df[category_key] == cat]
                if subcat != 'All':
                    subcategory_key = 'SubCategory_zh' if lang == "中文" else 'SubCategory'
                    temp_df = temp_df[temp_df[subcategory_key] == subcat]
                available_recipes = list(set(temp_df["RecipeDisplay"].unique()) - used_recipes)
                if len(available_recipes) == 0:
                    st.warning(f"第 {len(selected_recipes)+1} 道餐點無符合條件的食譜，將跳過。" if lang == "中文" else f"No recipes match the criteria for dish {len(selected_recipes)+1}, skipping.")
                    continue
                selected_recipe = random.choice(available_recipes)
                selected_recipes.append(selected_recipe)
                used_recipes.add(selected_recipe)
            if selected_recipes:
                st.session_state.selected = selected_recipes
                st.success(f"已隨機挑選 {len(selected_recipes)} 道餐點！" if lang == "中文" else f"Randomly selected {len(selected_recipes)} dishes!")
            else:
                st.error("無符合條件的食譜可選取。" if lang == "中文" else "No recipes match the criteria.")

# Advanced Filter Section (篩選)
with st.expander("🔍 進階篩選" if lang == "中文" else "🔍 Advanced Filters", expanded=False):
    category_display = "類別 (非必選)" if lang == "中文" else "Category (Optional)"
    style_display = "風格 (非必選)" if lang == "中文" else "Style (Optional)"
    category_options = ['All'] + sorted(recipes_df['Category_zh' if lang == "中文" else 'Category'].dropna().unique())
    style_options = ['All'] + sorted(recipes_df['SubCategory_zh' if lang == "中文" else 'SubCategory'].dropna().unique())
    selected_category = st.selectbox(category_display, category_options, index=category_options.index(st.session_state.selected_category))
    if selected_category != 'All':
        category_key = 'Category_zh' if lang == "中文" else 'Category'
        filtered_recipes = recipes_df[recipes_df[category_key] == selected_category]
        available_styles = ['All'] + sorted(filtered_recipes['SubCategory_zh' if lang == "中文" else 'SubCategory'].dropna().unique())
        selected_subcategory = st.selectbox(style_display, available_styles, index=available_styles.index(st.session_state.selected_subcategory) if st.session_state.selected_subcategory in available_styles else 0)
    else:
        selected_subcategory = st.selectbox(style_display, style_options, index=style_options.index(st.session_state.selected_subcategory))
    st.session_state.selected_category = selected_category
    st.session_state.selected_subcategory = selected_subcategory
    if st.button("清除篩選" if lang == "中文" else "Clear Filters"):
        st.session_state.selected_category = 'All'
        st.session_state.selected_subcategory = 'All'
        st.rerun()

# Display selected recipes (選擇食譜)
if len(recipe_options) > 0:
    valid_selected = [item for item in st.session_state.selected if item in recipe_options]
    selected = st.multiselect(
        "請選擇食譜" if lang == "中文" else "Select Recipe",
        recipe_options,
        default=valid_selected
    )
    st.session_state.selected = selected
else:
    selected = []
    st.session_state.selected = []
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
        image_url = rec_df["ImageURL"].iloc[0]
        if isinstance(image_url, str):
            if image_url.startswith("http"):
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
                    headers = {
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                        "Referer": "https://imgur.com/"
                    }
                    resp = requests.get(display_url, headers=headers)
                    img = Image.open(BytesIO(resp.content))
                    img = resize_image_with_aspect_ratio(img)  # Use new resize function to maintain aspect ratio
                    st.image(img)
                except Exception as e:
                    st.error(f"無法載入圖片：{e}")
                    st.markdown(f'<img src="{display_url}" style="max-width:500px; max-height:700px; object-fit:contain;">', unsafe_allow_html=True)
            else:
                image_path = Path(__file__).parent / image_url
                if image_path.exists():
                    img = Image.open(image_path)
                    img = resize_image_with_aspect_ratio(img)  # Use new resize function to maintain aspect ratio
                    st.image(img)
                else:
                    st.error(f"本地圖片路徑不存在：{image_path}")
        else:
            st.info("此食譜無圖片")
        info = rec_df.iloc[0][["Portion", "Method"]]
        portion = f"{info['Portion']} x{mult}"
        recipe_steps = steps_df[steps_df["RecipeID"] == recipe_id]
        total_recipe_time = recipe_steps[recipe_steps["Parallel"] == False]["CycleTime"].sum() if 'Parallel' in recipe_steps.columns and 'CycleTime' in recipe_steps.columns else 0
        if lang == "中文":
            st.markdown(f"### 🍽️ {recipe} - 👥 分量：{portion}")
            st.markdown(f"🍳 做法：{info['Method']}")
            st.markdown(f"⏱️ 預估時間：{total_recipe_time} 分鐘")
        else:
            st.markdown(f"### 🍽️ {recipe} - 👥 Portion: {portion}")
            st.markdown(f"🍳 Method: {info['Method']}")
            st.markdown(f"⏱️ Estimated Time: {total_recipe_time} min")
        st.subheader("🧰 工具清單" if lang == "中文" else "🧰 Tool List")
        recipe_tools = tools_df[tools_df["RecipeID"] == recipe_id]
        if recipe_tools.empty:
            st.info("工具資料待補" if lang == "中文" else "Tool data to be added")
        else:
            if lang == "中文":
                tool_display = recipe_tools[["ToolName_zh"]]
                tool_display.columns = ["工具"]
                if "Optional" in recipe_tools.columns:
                    tool_display["選用"] = recipe_tools["Optional"].apply(lambda x: "✓" if x else "")
                else:
                    tool_display["選用"] = ""
            else:
                tool_display = recipe_tools[["ToolName"]]
                tool_display.columns = ["Tool"]
                if "Optional" in recipe_tools.columns:
                    tool_display["Optional"] = recipe_tools["Optional"].apply(lambda x: "(optional)" if x else "")
                else:
                    tool_display["Optional"] = ""
            st.table(tool_display.reset_index(drop=True))
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
        st.subheader("📋 生產流程" if lang == "中文" else "📋 Sequence")
        step_data = steps_df[steps_df["RecipeID"] == recipe_id]
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
            instruction_col = "說明" if lang == "中文" else "Instruction"
            step_data[instruction_col] = step_data[instruction_col].apply(lambda x: str(x).replace('\n', '<br>').replace('; ', '<br>') if pd.notnull(x) else x)
            sequence_data = []
            last_part = None
            for index, row in step_data.iterrows():
                current_part = row["部位" if lang == "中文" else "Part"]
                if current_part != last_part:
                    sequence_data.append(row)
                    last_part = current_part
                else:
                    new_row = row.copy()
                    new_row["部位" if lang == "中文" else "Part"] = ""
                    sequence_data.append(new_row)
            sequence_df = pd.DataFrame(sequence_data)
            if "並行" in sequence_df.columns if lang == "中文" else "Parallel" in sequence_df.columns:
                sequence_df["並行" if lang == "中文" else "Parallel"] = sequence_df["並行" if lang == "中文" else "Parallel"].apply(lambda x: "✓" if x else "")
            st.markdown(sequence_df.to_html(escape=False, index=False), unsafe_allow_html=True)
    st.markdown("---")
    st.subheader("📝 採購清單" if lang == "中文" else "📝 Procurement")
    all_df = filtered_df[filtered_df["RecipeDisplay"].isin(selected)].copy()
    all_df["Multiplier"] = all_df["RecipeDisplay"].map(multipliers)
    all_df["TotalAmount"] = all_df["Amount"] * all_df["Multiplier"]
    ingredient_lines = []
    if lang == "中文":
        all_df["食材"] = all_df["Ingredient_zh"]
        summary = all_df.groupby(["食材", "Unit", "Optional"])["TotalAmount"].sum().reset_index()
        summary["數量"] = summary["TotalAmount"].apply(format_quantity)
        summary["選用"] = summary["Optional"].apply(lambda x: "✓" if x else "")
        summary = summary[["食材", "數量", "Unit", "選用"]]
        summary.columns = ["食材", "數量", "單位", "選用"]
        ingredient_lines = [f"{row['食材']}: {row['數量']}{row['單位']}" + (" (選用)" if row['選用'] else "") for _, row in summary.iterrows()]
    else:
        summary = all_df.groupby(["Ingredient", "Unit", "Optional"])["TotalAmount"].sum().reset_index()
        summary["Quantity"] = summary["TotalAmount"].apply(format_quantity)
        summary["Optional"] = summary["Optional"].apply(lambda x: "✓" if x else "")
        summary = summary[["Ingredient", "Quantity", "Unit", "Optional"]]
        ingredient_lines = [f"{row['Ingredient']}: {row['Quantity']}{row['Unit']}" + (" (optional)" if row['Optional'] else "") for _, row in summary.iterrows()]
    tool_lines = []
    all_tools = tools_df[tools_df["RecipeID"].isin(selected_ids)].copy()
    if not all_tools.empty:
        if lang == "中文":
            tool_summary = all_tools.groupby(["ToolName_zh", "Optional"]).size().reset_index(name="Count")
            if "Optional" in all_tools.columns:
                tool_summary["選用"] = tool_summary["Optional"].apply(lambda x: "✓" if x else "")
            else:
                tool_summary["選用"] = ""
            tool_lines = [f"{row['ToolName_zh']}" + (" (選用)" if row['選用'] else "") for _, row in tool_summary.iterrows()]
        else:
            tool_summary = all_tools.groupby(["ToolName", "Optional"]).size().reset_index(name="Count")
            if "Optional" in all_tools.columns:
                tool_summary["Optional"] = tool_summary["Optional"].apply(lambda x: "(optional)" if x else "")
            else:
                tool_summary["Optional"] = ""
            tool_lines = [f"{row['ToolName']}" + (" (optional)" if row['Optional'] else "") for _, row in tool_summary.iterrows()]
    st.markdown(
        f'<span style="margin-right: 5px;">•</span><span style="font-size: 1rem; font-weight: bold;">{"食材總和" if lang == "中文" else "Ingredients Summary"}</span>',
        unsafe_allow_html=True
    )
    st.code("\n".join(ingredient_lines))
    st.markdown(
        f'<span style="margin-right: 5px;">•</span><span style="font-size: 1rem; font-weight: bold;">{"工具總和" if lang == "中文" else "Tools Summary"}</span>',
        unsafe_allow_html=True
    )
    if tool_lines:
        st.code("\n".join(tool_lines))
    else:
        st.info("工具資料待補" if lang == "中文" else "Tool data to be added")
    st.markdown("---")
    st.markdown("### ⏱️ 預估總時間" if lang == "中文" else "### ⏱️ Estimated Total Time")
    total_time = 0
    for recipe_id in selected_ids:
        recipe_steps = steps_df[steps_df["RecipeID"] == recipe_id]
        if 'Parallel' in recipe_steps.columns and 'CycleTime' in recipe_steps.columns:
            total_time += recipe_steps[recipe_steps["Parallel"] == False]["CycleTime"].sum()
    st.markdown(f"{total_time} 分鐘" if lang == "中文" else f"{total_time} min")
else:
    st.info("請選擇至少一道食譜" if lang == "中文" else "Please select at least one recipe.")