import streamlit as st
from pathlib import Path
import pandas as pd
import re
from PIL import Image
import random
import json
from datetime import datetime

# Set page configuration
st.set_page_config(page_title="🧑‍🍳Chef Tai🛠️", layout="centered")

# ── 多語言文字字典 ────────────────────────────────────────────────────────────
LANG = {
    "中文": {
        "light_mode_tip":       "💡 建議使用淺色模式以獲得最佳體驗",
        "choose_lang":          "選擇語言 / Choose Language",
        "today_visits":         "今日訪客數",
        "total_visits":         "歷史總訪客數",
        "surprise_pick":        "❓ 驚喜挑選",
        "select_mode":          "選擇模式",
        "basic_mode":           "基本模式",
        "advanced_mode":        "進階模式",
        "num_dishes":           "選擇隨機餐點數量",
        "random_pick":          "隨機挑選",
        "no_recipes_filter":    "目前篩選條件下無可用食譜",
        "randomly_selected":    lambda n: f"已隨機挑選 {n} 道餐點！",
        "dish_settings":        lambda i: f"**第 {i} 道餐點設定**",
        "category_dish":        lambda i: f"類別 (第 {i} 道)",
        "style_dish":           lambda i: f"風格 (第 {i} 道)",
        "skip_dish":            lambda i: f"第 {i} 道餐點無符合條件的食譜，將跳過。",
        "no_match":             "無符合條件的食譜可選取。",
        "adv_filters":          "🔍 進階篩選",
        "category":             "類別 (非必選)",
        "style":                "風格 (非必選)",
        "clear_filters":        "清除篩選",
        "select_recipe":        "請選擇食譜（可輸入搜尋）",
        "no_recipes":           "目前篩選條件下無可用食譜",
        "multiplier_label":     "份量倍率",
        "base_portion":         "單位份數",
        "portion_label":        "份數",
        "no_image":             "此食譜無圖片",
        "img_load_err":         "無法載入圖片：",
        "local_img_err":        "本地圖片路徑不存在：",
        "portion":              "份量",
        "method":               "做法",
        "est_time":             "預估時間",
        "min":                  "分鐘",
        "tool_list":            "🧰 工具清單",
        "tool_pending":         "工具資料待補",
        "tool_col":             "工具",
        "optional_col":         "非必要",
        "bom":                  "🫜 BoM 物料表",
        "ingredient_col":       "食材",
        "qty_col":              "數量",
        "unit_col":             "單位",
        "sequence":             "📋 生產流程",
        "step_pending":         "步驟資料待補",
        "step_col":             "步驟",
        "part_col":             "部位",
        "instruction_col":      "說明",
        "time_col":             "時間",
        "parallel_col":         "並行",
        "procurement":          "📝 採購清單",
        "ingredient_summary":   "食材總和",
        "tool_summary":         "工具總和",
        "total_time":           "### ⏱️ 預估總時間",
        "select_one":           "請選擇至少一道食譜",
    },
    "English": {
        "light_mode_tip":       "💡 Suggest using light mode for the best experience",
        "choose_lang":          "選擇語言 / Choose Language",
        "today_visits":         "Today's Visits",
        "total_visits":         "Total Visits",
        "surprise_pick":        "❓ Surprise Pick",
        "select_mode":          "Select Mode",
        "basic_mode":           "Basic Mode",
        "advanced_mode":        "Advanced Mode",
        "num_dishes":           "Number of Dishes to Randomize",
        "random_pick":          "Random Pick",
        "no_recipes_filter":    "No recipes available under current filters.",
        "randomly_selected":    lambda n: f"Randomly selected {n} dishes!",
        "dish_settings":        lambda i: f"**Dish {i} Settings**",
        "category_dish":        lambda i: f"Category (Dish {i})",
        "style_dish":           lambda i: f"Style (Dish {i})",
        "skip_dish":            lambda i: f"No recipes match the criteria for dish {i}, skipping.",
        "no_match":             "No recipes match the criteria.",
        "adv_filters":          "🔍 Advanced Filters",
        "category":             "Category (Optional)",
        "style":                "Style (Optional)",
        "clear_filters":        "Clear Filters",
        "select_recipe":        "Select Recipe (type to search)",
        "no_recipes":           "No recipes available under current filters.",
        "multiplier_label":     "Multiplier",
        "base_portion":         "Base Portion",
        "portion_label":        "Portion",
        "no_image":             "No image for this recipe",
        "img_load_err":         "Failed to load image: ",
        "local_img_err":        "Local image path not found: ",
        "portion":              "Portion",
        "method":               "Method",
        "est_time":             "Estimated Time",
        "min":                  "min",
        "tool_list":            "🧰 Tool List",
        "tool_pending":         "Tool data to be added",
        "tool_col":             "Tool",
        "optional_col":         "Optional",
        "bom":                  "🫜 BoM (Bill of Materials)",
        "ingredient_col":       "Ingredient",
        "qty_col":              "Quantity",
        "unit_col":             "Unit",
        "sequence":             "📋 Sequence",
        "step_pending":         "Step data to be added",
        "step_col":             "Step",
        "part_col":             "Part",
        "instruction_col":      "Instruction",
        "time_col":             "CycleTime",
        "parallel_col":         "Parallel",
        "procurement":          "📝 Procurement",
        "ingredient_summary":   "Ingredients Summary",
        "tool_summary":         "Tools Summary",
        "total_time":           "### ⏱️ Estimated Total Time",
        "select_one":           "Please select at least one recipe.",
    },
}

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── 背景色 ── */
[data-testid="stAppViewContainer"] {
    background-color: #d8d4c0 !important;
}

/* ── 內容文字黑色（不影響互動元件） ── */
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

/* ── Slider 數值文字 ── */
[data-testid="stSlider"] .stSliderValue { color: #000 !important; }
[data-testid="stNumberInput"] label,
[data-testid="stNumberInput"] input      { color: #000 !important; }

/* ── Dark mode 覆寫 ── */
@media (prefers-color-scheme: dark) {
    [data-testid="stButton"] button,
    [data-testid="stButton"] button p    { color: #fff !important; }
    [data-testid="stNumberInput"] label,
    [data-testid="stNumberInput"] input  { color: #fff !important; }
    [data-testid="stNumberInput"] input  {
        background-color: #444 !important;
        border: 1px solid #666 !important;
    }
    [data-testid="stSlider"] .stSliderValue { color: #fff !important; }
}

/* ── 手機字型縮放 ── */
@media (max-width: 600px) {
    [data-testid="stAppViewContainer"] h1   { font-size: 2rem !important; }
    [data-testid="stAppViewContainer"] h2,
    [data-testid="stAppViewContainer"] h3   { font-size: 1.2rem !important; }
}

/* ── Sequence 表格欄寬 ── */
table[data-testid="stTable"] td:nth-child(1) { min-width:150px; max-width:150px; word-break:normal; }
table[data-testid="stTable"] td:nth-child(2) { min-width:50px;  max-width:50px;  word-break:normal; }
table[data-testid="stTable"] td:nth-child(3) { min-width:300px;                  word-break:normal; }
table[data-testid="stTable"] td:nth-child(4) { min-width:80px;  max-width:80px;  word-break:normal; }
table[data-testid="stTable"] td:nth-child(5) { min-width:60px;  max-width:60px;  word-break:normal; }

/* ══ 手機選單體驗：multiselect dropdown 往上展開 ══
   當鍵盤彈出佔據下半畫面時，選項清單改為在輸入框上方顯示，
   並限制最大高度讓其不被鍵盤遮住。                          */
[data-baseweb="popover"] {
    /* 強制讓 popover 在上方展開 */
    transform-origin: bottom center !important;
}
[data-baseweb="menu"] {
    max-height: 35vh !important;   /* 最多佔螢幕高度 35%，鍵盤彈出後仍可見 */
    overflow-y: auto  !important;
}
/* 讓每個選項在手機上更容易點按 */
@media (max-width: 600px) {
    [data-baseweb="option"] {
        padding-top:    14px !important;
        padding-bottom: 14px !important;
        font-size: 1rem !important;
    }
    /* multiselect 輸入框放大，方便觸控 */
    [data-baseweb="select"] input {
        font-size: 1rem !important;
    }
}
</style>
""", unsafe_allow_html=True)

# ── 語言選擇（最先執行，後續所有 UI 都依賴它） ─────────────────────────────
lang = st.radio("選擇語言 / Choose Language", ["中文", "English"])
T = LANG[lang]

# ── Header 圖片 ───────────────────────────────────────────────────────────────
header_path = Path(__file__).parent / 'chef_tai_header_centered.png'
if header_path.exists():
    st.image(str(header_path), use_container_width=True)

st.markdown(T["light_mode_tip"])

# ── 訪客計數（用 session_state 確保每次 session 只計一次） ───────────────────
visit_file   = Path(__file__).parent / 'visit_history.json'
current_date = datetime.now().strftime("%Y-%m-%d")

if visit_file.exists():
    with open(visit_file, 'r') as f:
        visit_data = json.load(f)
else:
    visit_data = {"visits": []}

# ★ Bug 修正：只在新 session 第一次執行時才記錄訪客
if 'visit_counted' not in st.session_state:
    st.session_state.visit_counted = True
    current_timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    visit_data["visits"].append({"timestamp": current_timestamp})
    with open(visit_file, 'w') as f:
        json.dump(visit_data, f, indent=4)

total_visits = len(visit_data["visits"])
today_visits = sum(1 for v in visit_data["visits"] if v["timestamp"].startswith(current_date))
st.markdown(f"**{T['today_visits']}：{today_visits} | {T['total_visits']}：{total_visits}**")

# ── 標題 ─────────────────────────────────────────────────────────────────────
st.title("🧑‍🍳🛠️ Flavor Engine")

# ── 工具函式 ─────────────────────────────────────────────────────────────────
def format_quantity(val):
    return str(int(val)) if float(val).is_integer() else f"{val:.1f}"

def snap_multiplier(value):
    # 以 0.5 為單位：0, 0.5, 1, 1.5, 2, ...
    return round(value * 2) / 2

def resize_image_with_aspect_ratio(image, max_width=500, max_height=700):
    w, h = image.size
    ratio = w / h
    if w > max_width:
        w, h = max_width, int(max_width / ratio)
    if h > max_height:
        h, w = max_height, int(max_height * ratio)
    return image.resize((w, h), Image.Resampling.LANCZOS)

# ── 資料載入 ─────────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    # ★ Bug 修正：使用相對於 __file__ 的路徑，避免工作目錄不同導致錯誤
    excel_path = Path(__file__).parent / "Recipe_Database_Corrected.xlsx"
    df = pd.read_excel(excel_path, sheet_name=None)
    ingredients    = df["Ingredients"]
    recipes        = df["Recipes"]
    components     = df["Components"]
    ingredient_dict = df["IngredientDict"]
    steps          = df["Steps"]
    tools          = df.get("Tools", pd.DataFrame(
        columns=["RecipeID", "ToolName", "ToolName_zh", "Optional"]))
    merged = (
        ingredients
        .merge(components.drop(columns=["RecipeID"]), on="ComponentID", how="left")
        .merge(recipes,          on="RecipeID",    how="left")
        .merge(ingredient_dict,  on="Ingredient",  how="left")
    )
    merged["RecipeName"]    = merged["RecipeName"].str.replace(r'\*\*', '', regex=True)
    merged["RecipeName_zh"] = merged["RecipeName_zh"].str.replace(r'\*\*', '', regex=True)
    return merged, recipes, steps, tools

df, recipes_df, steps_df, tools_df = load_data()

# ── Session state 初始化 ──────────────────────────────────────────────────────
for key, default in [('selected_category', 'All'),
                     ('selected_subcategory', 'All'),
                     ('selected', [])]:
    if key not in st.session_state:
        st.session_state[key] = default

# ── filtered_df 在 expander 外定義，確保採購清單也能使用 ─────────────────────
# ★ Bug 修正：原本定義在 expander 內，scope 不一致
filtered_df = df.copy()
cat_key    = 'Category_zh'    if lang == "中文" else 'Category'
subcat_key = 'SubCategory_zh' if lang == "中文" else 'SubCategory'
if st.session_state.selected_category != 'All':
    filtered_df = filtered_df[filtered_df[cat_key] == st.session_state.selected_category]
if st.session_state.selected_subcategory != 'All':
    filtered_df = filtered_df[filtered_df[subcat_key] == st.session_state.selected_subcategory]
filtered_df["RecipeDisplay"] = (
    filtered_df["RecipeName_zh"] if lang == "中文" else filtered_df["RecipeName"]
)
recipe_options = filtered_df["RecipeDisplay"].unique()

# ── 驚喜挑選 ─────────────────────────────────────────────────────────────────
with st.expander(T["surprise_pick"], expanded=False):
    mode = st.radio(T["select_mode"], [T["basic_mode"], T["advanced_mode"]])

    if mode == T["basic_mode"]:
        num_dishes = st.number_input(T["num_dishes"], min_value=1, max_value=5, value=1)
        if st.button(T["random_pick"], key="basic_random"):
            available = list(recipe_options)
            if not available:
                st.error(T["no_recipes_filter"])
            else:
                n = min(int(num_dishes), len(available))
                st.session_state.selected = random.sample(available, n)
                st.success(T["randomly_selected"](n))
    else:
        num_dishes = st.number_input(T["num_dishes"], min_value=1, max_value=5, value=1, key="adv_num")
        filters = []
        for i in range(int(num_dishes)):
            st.markdown(T["dish_settings"](i + 1))
            cat = st.selectbox(
                T["category_dish"](i + 1),
                ['All'] + sorted(recipes_df[cat_key].dropna().unique()),
                key=f"adv_category_{i}"
            )
            if cat != 'All':
                fs = recipes_df[recipes_df[cat_key] == cat]
                styles = ['All'] + sorted(fs[subcat_key].dropna().unique())
            else:
                styles = ['All'] + sorted(recipes_df[subcat_key].dropna().unique())
            subcat = st.selectbox(T["style_dish"](i + 1), styles, key=f"adv_subcategory_{i}")
            filters.append((cat, subcat))

        if st.button(T["random_pick"], key="adv_random"):
            selected_recipes, used = [], set()
            for idx, (cat, subcat) in enumerate(filters):
                tmp = filtered_df.copy()
                if cat != 'All':
                    tmp = tmp[tmp[cat_key] == cat]
                if subcat != 'All':
                    tmp = tmp[tmp[subcat_key] == subcat]
                available = list(set(tmp["RecipeDisplay"].unique()) - used)
                if not available:
                    st.warning(T["skip_dish"](idx + 1))
                    continue
                pick = random.choice(available)
                selected_recipes.append(pick)
                used.add(pick)
            if selected_recipes:
                st.session_state.selected = selected_recipes
                st.success(T["randomly_selected"](len(selected_recipes)))
            else:
                st.error(T["no_match"])

# ── 進階篩選 ─────────────────────────────────────────────────────────────────
with st.expander(T["adv_filters"], expanded=False):
    cat_options = ['All'] + sorted(recipes_df[cat_key].dropna().unique())
    sel_cat = st.selectbox(
        T["category"], cat_options,
        index=cat_options.index(st.session_state.selected_category)
        if st.session_state.selected_category in cat_options else 0
    )
    if sel_cat != 'All':
        avail_styles = ['All'] + sorted(
            recipes_df[recipes_df[cat_key] == sel_cat][subcat_key].dropna().unique())
    else:
        avail_styles = ['All'] + sorted(recipes_df[subcat_key].dropna().unique())
    sel_sub = st.selectbox(
        T["style"], avail_styles,
        index=avail_styles.index(st.session_state.selected_subcategory)
        if st.session_state.selected_subcategory in avail_styles else 0
    )
    st.session_state.selected_category    = sel_cat
    st.session_state.selected_subcategory = sel_sub
    if st.button(T["clear_filters"]):
        st.session_state.selected_category    = 'All'
        st.session_state.selected_subcategory = 'All'
        st.rerun()

# ── 食譜多選（手機優化：搜尋提示 + dropdown 往上展開由 CSS 處理） ────────────
if len(recipe_options) > 0:
    valid_selected = [i for i in st.session_state.selected if i in recipe_options]
    selected = st.multiselect(
        T["select_recipe"],   # label 已提示可輸入搜尋
        recipe_options,
        default=valid_selected
    )
    st.session_state.selected = selected
else:
    selected = []
    st.session_state.selected = []
    st.info(T["no_recipes"])

# ── 食譜內容展示 ──────────────────────────────────────────────────────────────
if selected:
    multipliers = {}
    for recipe in selected:
        rec_df = filtered_df[filtered_df["RecipeDisplay"] == recipe].copy()
        base_portion = rec_df.iloc[0]["Portion"]
        key = f"multiplier_{recipe}"
        if key not in st.session_state:
            st.session_state[key] = 1.0
        if isinstance(st.session_state[key], list):
            st.session_state[key] = st.session_state[key][0] if st.session_state[key] else 1.0

        raw_mult = st.slider(
            f"{recipe} - {T['multiplier_label']}",
            min_value=0.0, max_value=10.0,
            value=float(st.session_state[key]), step=0.5,
            key=f"slider_{recipe}"
        )
        mult = snap_multiplier(raw_mult)
        st.session_state[key] = float(mult)
        st.markdown(
            f"**{recipe} - {T['base_portion']}: {base_portion} - "
            f"{T['portion_label']}: {base_portion} x {mult}**"
        )
        multipliers[recipe] = mult

    selected_ids = filtered_df[filtered_df["RecipeDisplay"].isin(selected)]["RecipeID"].unique()

    for recipe in selected:
        rec_df    = filtered_df[filtered_df["RecipeDisplay"] == recipe].copy()
        recipe_id = rec_df["RecipeID"].iloc[0]
        mult      = multipliers[recipe]
        image_url = rec_df["ImageURL"].iloc[0]

        # ── 圖片 ──
        if isinstance(image_url, str):
            if image_url.startswith("http"):
                # 直接傳 URL 給瀏覽器渲染，不經過 Python requests
                # 避免網路下載觸發 rerun 造成畫面閃爍
                st.markdown(
                    f'<img src="{image_url}" style="max-width:500px;max-height:700px;object-fit:contain;">',
                    unsafe_allow_html=True
                )
            else:
                image_path = Path(__file__).parent / image_url
                if image_path.exists():
                    img = Image.open(image_path)
                    img = resize_image_with_aspect_ratio(img)
                    st.image(img)
                else:
                    st.info(T["no_image"])
        else:
            st.info(T["no_image"])

        # ── 基本資訊 ──
        info = rec_df.iloc[0][["Portion", "Method"]]
        portion = f"{info['Portion']} x{mult}"
        recipe_steps    = steps_df[steps_df["RecipeID"] == recipe_id]
        total_recipe_time = (
            recipe_steps[recipe_steps["Parallel"] == False]["CycleTime"].sum()
            if 'Parallel' in recipe_steps.columns and 'CycleTime' in recipe_steps.columns
            else 0
        )
        st.markdown(f"### 🍽️ {recipe} - 👥 {T['portion']}：{portion}")
        st.markdown(f"🍳 {T['method']}：{info['Method']}")
        st.markdown(f"⏱️ {T['est_time']}：{total_recipe_time} {T['min']}")

        # ── 工具清單 ──
        st.subheader(T["tool_list"])
        recipe_tools = tools_df[tools_df["RecipeID"] == recipe_id]
        if recipe_tools.empty:
            st.info(T["tool_pending"])
        else:
            name_col = "ToolName_zh" if lang == "中文" else "ToolName"
            tool_display = recipe_tools[[name_col]].copy()
            tool_display.columns = [T["tool_col"]]
            # ★ Bug 修正：原本中文分支有 typo "非必要非必要"
            tool_display[T["optional_col"]] = (
                recipe_tools["Optional"].apply(lambda x: "✓" if x else "")
                if "Optional" in recipe_tools.columns
                else ""
            )
            st.table(tool_display.reset_index(drop=True))

        # ── BoM 物料表 ──
        st.subheader(T["bom"])
        for comp in rec_df["ComponentName"].unique():
            comp_df      = rec_df[rec_df["ComponentName"] == comp]
            comp_display = comp_df["ComponentName_zh"].iloc[0] if lang == "中文" else comp
            if lang == "中文":
                comp_df = comp_df.copy()
                comp_df["食材"] = comp_df["Ingredient_zh"]
                display = (
                    comp_df.groupby(["食材", "Unit", "Optional"])["Amount"]
                    .sum().mul(mult).reset_index()
                )
                display[T["qty_col"]]      = display["Amount"].apply(format_quantity)
                display[T["optional_col"]] = display["Optional"].apply(lambda x: "✓" if x else "")
                display = display[["食材", T["qty_col"], "Unit", T["optional_col"]]]
                display.columns = [T["ingredient_col"], T["qty_col"], T["unit_col"], T["optional_col"]]
            else:
                display = (
                    comp_df.groupby(["Ingredient", "Unit", "Optional"])["Amount"]
                    .sum().mul(mult).reset_index()
                )
                display[T["qty_col"]]      = display["Amount"].apply(format_quantity)
                display[T["optional_col"]] = display["Optional"].apply(lambda x: "✓" if x else "")
                display = display[["Ingredient", T["qty_col"], "Unit", T["optional_col"]]]
            st.subheader(f"• {comp_display}")
            st.table(display.reset_index(drop=True))

        # ── 生產流程 ──
        st.subheader(T["sequence"])
        step_data = steps_df[steps_df["RecipeID"] == recipe_id]
        part_col_src        = "Part_zh"        if lang == "中文" else "Part"
        instruction_col_src = "Instruction_zh" if lang == "中文" else "Instruction_en"
        required_columns    = ["StepOrder", part_col_src, instruction_col_src]
        if step_data.empty or not all(c in step_data.columns for c in required_columns):
            st.info(T["step_pending"])
        else:
            extra = (["CycleTime", "Parallel"]
                     if "CycleTime" in step_data.columns and "Parallel" in step_data.columns
                     else [])
            step_data = step_data[required_columns + extra].rename(columns={
                "StepOrder":        T["step_col"],
                part_col_src:       T["part_col"],
                instruction_col_src: T["instruction_col"],
                "CycleTime":        T["time_col"],
                "Parallel":         T["parallel_col"],
            })
            instr_col = T["instruction_col"]
            step_data[instr_col] = step_data[instr_col].apply(
                lambda x: str(x).replace('\n', '<br>').replace('; ', '<br>') if pd.notnull(x) else x
            )
            # 合併重複 Part 欄位
            sequence_data, last_part = [], None
            part_col = T["part_col"]
            for _, row in step_data.iterrows():
                cur = row[part_col]
                if cur != last_part:
                    sequence_data.append(row)
                    last_part = cur
                else:
                    r = row.copy()
                    r[part_col] = ""
                    sequence_data.append(r)
            sequence_df = pd.DataFrame(sequence_data)
            par_col = T["parallel_col"]
            if par_col in sequence_df.columns:
                sequence_df[par_col] = sequence_df[par_col].apply(lambda x: "✓" if x else "")
            st.markdown(sequence_df.to_html(escape=False, index=False), unsafe_allow_html=True)

    # ── 採購清單 ─────────────────────────────────────────────────────────────
    st.markdown("---")
    st.subheader(T["procurement"])
    all_df = filtered_df[filtered_df["RecipeDisplay"].isin(selected)].copy()
    all_df["Multiplier"]  = all_df["RecipeDisplay"].map(multipliers)
    all_df["TotalAmount"] = all_df["Amount"] * all_df["Multiplier"]

    if lang == "中文":
        all_df["食材"] = all_df["Ingredient_zh"]
        summary = all_df.groupby(["食材", "Unit", "Optional"])["TotalAmount"].sum().reset_index()
        summary["數量"]   = summary["TotalAmount"].apply(format_quantity)
        summary["非必要"] = summary["Optional"].apply(lambda x: "✓" if x else "")
        summary = summary[["食材", "數量", "Unit", "非必要"]]
        summary.columns = ["食材", "數量", "單位", "非必要"]
        ingredient_lines = [
            f"{r['食材']}: {r['數量']}{r['單位']}" + (" (非必要)" if r['非必要'] else "")
            for _, r in summary.iterrows()
        ]
    else:
        summary = all_df.groupby(["Ingredient", "Unit", "Optional"])["TotalAmount"].sum().reset_index()
        summary["Quantity"] = summary["TotalAmount"].apply(format_quantity)
        summary["Optional"] = summary["Optional"].apply(lambda x: "✓" if x else "")
        summary = summary[["Ingredient", "Quantity", "Unit", "Optional"]]
        ingredient_lines = [
            f"{r['Ingredient']}: {r['Quantity']}{r['Unit']}" + (" (optional)" if r['Optional'] else "")
            for _, r in summary.iterrows()
        ]

    all_tools = tools_df[tools_df["RecipeID"].isin(selected_ids)].copy()
    tool_lines = []
    if not all_tools.empty:
        if lang == "中文":
            ts = all_tools.groupby(["ToolName_zh", "Optional"]).size().reset_index(name="Count")
            ts["非必要"] = ts["Optional"].apply(lambda x: "✓" if x else "") if "Optional" in all_tools.columns else ""
            tool_lines = [f"{r['ToolName_zh']}" + (" (非必要)" if r['非必要'] else "") for _, r in ts.iterrows()]
        else:
            ts = all_tools.groupby(["ToolName", "Optional"]).size().reset_index(name="Count")
            ts["Opt"] = ts["Optional"].apply(lambda x: "(optional)" if x else "") if "Optional" in all_tools.columns else ""
            tool_lines = [f"{r['ToolName']}" + (f" {r['Opt']}" if r['Opt'] else "") for _, r in ts.iterrows()]

    st.markdown(f'<span style="margin-right:5px;">•</span>'
                f'<span style="font-size:1rem;font-weight:bold;">{T["ingredient_summary"]}</span>',
                unsafe_allow_html=True)
    st.code("\n".join(ingredient_lines))

    st.markdown(f'<span style="margin-right:5px;">•</span>'
                f'<span style="font-size:1rem;font-weight:bold;">{T["tool_summary"]}</span>',
                unsafe_allow_html=True)
    if tool_lines:
        st.code("\n".join(tool_lines))
    else:
        st.info(T["tool_pending"])

    # ── 預估總時間 ────────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown(T["total_time"])
    total_time = 0
    for rid in selected_ids:
        rs = steps_df[steps_df["RecipeID"] == rid]
        if 'Parallel' in rs.columns and 'CycleTime' in rs.columns:
            total_time += rs[rs["Parallel"] == False]["CycleTime"].sum()
    st.markdown(f"{total_time} {T['min']}")

else:
    st.info(T["select_one"])