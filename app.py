import streamlit as st
from pathlib import Path
import pandas as pd
import re
import random

st.set_page_config(page_title="🧑‍🍳Chef Tai🛠️", layout="centered")

st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background-color: #d8d4c0 !important; }
[data-testid="stAppViewContainer"] h1,
[data-testid="stAppViewContainer"] h2,
[data-testid="stAppViewContainer"] h3,
[data-testid="stAppViewContainer"] p,
[data-testid="stAppViewContainer"] li,
[data-testid="stAppViewContainer"] td,
[data-testid="stAppViewContainer"] th,
[data-testid="stAppViewContainer"] div.stMarkdown,
[data-testid="stAppViewContainer"] div.stInfo,
[data-testid="stAppViewContainer"] div.stCodeBlock { color: #000 !important; }
[data-testid="stSlider"] .stSliderValue { color: #000 !important; }
@media (prefers-color-scheme: dark) {
    [data-testid="stButton"] button,
    [data-testid="stButton"] button p { color: #fff !important; }
    [data-testid="stSlider"] .stSliderValue { color: #fff !important; }
}
@media (max-width: 600px) {
    [data-testid="stAppViewContainer"] h1 { font-size: 2rem !important; }
    [data-testid="stAppViewContainer"] h2,
    [data-testid="stAppViewContainer"] h3 { font-size: 1.2rem !important; }
    [data-baseweb="option"] { padding-top: 14px !important; padding-bottom: 14px !important; font-size: 1rem !important; }
}
[data-baseweb="menu"] { max-height: 35vh !important; overflow-y: auto !important; }
table[data-testid="stTable"] td:nth-child(1) { min-width:150px; max-width:150px; word-break:normal; }
table[data-testid="stTable"] td:nth-child(2) { min-width:50px;  max-width:50px;  word-break:normal; }
table[data-testid="stTable"] td:nth-child(3) { min-width:300px;                  word-break:normal; }
table[data-testid="stTable"] td:nth-child(4) { min-width:80px;  max-width:80px;  word-break:normal; }
table[data-testid="stTable"] td:nth-child(5) { min-width:60px;  max-width:60px;  word-break:normal; }
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────
header_path = Path(__file__).parent / 'chef_tai_header_centered.png'
if header_path.exists():
    st.image(str(header_path), use_container_width=True)

st.markdown("💡 建議使用淺色模式以獲得最佳體驗 / Suggest using light mode for the best experience")
lang = st.radio("選擇語言 / Choose Language", ["中文", "English"])
st.title("🧑‍🍳🛠️ Flavor Engine")

# ── 工具函式 ──────────────────────────────────────────────────────────────────
def format_quantity(val):
    return str(int(val)) if float(val).is_integer() else f"{val:.1f}"

# ── 資料載入 ──────────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    excel_path = Path(__file__).parent / "Recipe_Database_Corrected.xlsx"
    raw = pd.read_excel(excel_path, sheet_name=None)
    ingredients     = raw["Ingredients"]
    recipes         = raw["Recipes"]
    components      = raw["Components"]
    ingredient_dict = raw["IngredientDict"]
    steps           = raw["Steps"]
    tools           = raw.get("Tools", pd.DataFrame(
        columns=["RecipeID", "ToolName", "ToolName_zh", "Optional"]))
    merged = (
        ingredients
        .merge(components.drop(columns=["RecipeID"]), on="ComponentID", how="left")
        .merge(recipes,          on="RecipeID",   how="left")
        .merge(ingredient_dict,  on="Ingredient", how="left")
    )
    merged["RecipeName"]    = merged["RecipeName"].str.replace(r'\*\*', '', regex=True)
    merged["RecipeName_zh"] = merged["RecipeName_zh"].str.replace(r'\*\*', '', regex=True)
    recipes["RecipeName"]    = recipes["RecipeName"].str.replace(r'\*\*', '', regex=True)
    recipes["RecipeName_zh"] = recipes["RecipeName_zh"].str.replace(r'\*\*', '', regex=True)
    return merged, recipes, steps, tools

df, recipes_df, steps_df, tools_df = load_data()

# ── Session state 初始化 ──────────────────────────────────────────────────────
# 只用 session_state 存篩選條件和驚喜挑選的結果
# multiselect 本身完全用 Streamlit 原生 key，不手動寫回 session_state
for key, default in [
    ('selected_category', 'All'),
    ('selected_subcategory', 'All'),
    ('surprise_result', []),   # 驚喜挑選結果暫存
]:
    if key not in st.session_state:
        st.session_state[key] = default

cat_key     = 'Category_zh'    if lang == "中文" else 'Category'
subcat_key  = 'SubCategory_zh' if lang == "中文" else 'SubCategory'
display_col = 'RecipeName_zh'  if lang == "中文" else 'RecipeName'

# ── recipe_options：從 recipes_df 產生乾淨 list ───────────────────────────────
filtered_recipes = recipes_df.copy()
if st.session_state.selected_category != 'All':
    filtered_recipes = filtered_recipes[filtered_recipes[cat_key] == st.session_state.selected_category]
if st.session_state.selected_subcategory != 'All':
    filtered_recipes = filtered_recipes[filtered_recipes[subcat_key] == st.session_state.selected_subcategory]
recipe_options = list(filtered_recipes[display_col].unique())

# ── filtered_df：供 BoM / 步驟查詢 ───────────────────────────────────────────
df["RecipeDisplay"] = df[display_col]
filtered_df = df[df["RecipeDisplay"].isin(recipe_options)].copy()

# ── 驚喜挑選 ─────────────────────────────────────────────────────────────────
with st.expander("❓ 驚喜挑選" if lang == "中文" else "❓ Surprise Pick", expanded=False):
    mode = st.radio(
        "選擇模式" if lang == "中文" else "Select Mode",
        ["基本模式", "進階模式"] if lang == "中文" else ["Basic Mode", "Advanced Mode"]
    )
    if mode == ("基本模式" if lang == "中文" else "Basic Mode"):
        num_dishes = st.number_input(
            "選擇隨機餐點數量" if lang == "中文" else "Number of Dishes to Randomize",
            min_value=1, max_value=5, value=1
        )
        if st.button("隨機挑選" if lang == "中文" else "Random Pick", key="basic_random"):
            if not recipe_options:
                st.error("目前篩選條件下無可用食譜" if lang == "中文" else "No recipes available.")
            else:
                n = min(int(num_dishes), len(recipe_options))
                st.session_state.surprise_result = random.sample(recipe_options, n)
                st.rerun()
    else:
        num_dishes = st.number_input(
            "選擇隨機餐點數量" if lang == "中文" else "Number of Dishes to Randomize",
            min_value=1, max_value=5, value=1, key="adv_num"
        )
        filters = []
        for i in range(int(num_dishes)):
            st.markdown(f"**第 {i+1} 道餐點設定**" if lang == "中文" else f"**Dish {i+1} Settings**")
            cat = st.selectbox(
                f"類別 (第 {i+1} 道)" if lang == "中文" else f"Category (Dish {i+1})",
                ['All'] + sorted(recipes_df[cat_key].dropna().unique()),
                key=f"adv_cat_{i}"
            )
            styles = (
                ['All'] + sorted(recipes_df[recipes_df[cat_key] == cat][subcat_key].dropna().unique())
                if cat != 'All' else
                ['All'] + sorted(recipes_df[subcat_key].dropna().unique())
            )
            subcat = st.selectbox(
                f"風格 (第 {i+1} 道)" if lang == "中文" else f"Style (Dish {i+1})",
                styles, key=f"adv_sub_{i}"
            )
            filters.append((cat, subcat))

        if st.button("隨機挑選" if lang == "中文" else "Random Pick", key="adv_random"):
            picked, used = [], set()
            for idx, (cat, subcat) in enumerate(filters):
                pool = filtered_recipes.copy()
                if cat != 'All':
                    pool = pool[pool[cat_key] == cat]
                if subcat != 'All':
                    pool = pool[pool[subcat_key] == subcat]
                available = [r for r in pool[display_col].unique() if r not in used]
                if not available:
                    st.warning(f"第 {idx+1} 道無符合條件食譜，跳過。" if lang == "中文" else f"No match for dish {idx+1}, skipping.")
                    continue
                choice = random.choice(available)
                picked.append(choice)
                used.add(choice)
            if picked:
                st.session_state.surprise_result = picked
                st.rerun()
            else:
                st.error("無符合條件的食譜。" if lang == "中文" else "No recipes match the criteria.")

# ── 進階篩選 ─────────────────────────────────────────────────────────────────
with st.expander("🔍 進階篩選" if lang == "中文" else "🔍 Advanced Filters", expanded=False):
    cat_options = ['All'] + sorted(recipes_df[cat_key].dropna().unique())
    sel_cat = st.selectbox(
        "類別 (非必選)" if lang == "中文" else "Category (Optional)", cat_options,
        index=cat_options.index(st.session_state.selected_category)
        if st.session_state.selected_category in cat_options else 0
    )
    avail_styles = (
        ['All'] + sorted(recipes_df[recipes_df[cat_key] == sel_cat][subcat_key].dropna().unique())
        if sel_cat != 'All' else
        ['All'] + sorted(recipes_df[subcat_key].dropna().unique())
    )
    sel_sub = st.selectbox(
        "風格 (非必選)" if lang == "中文" else "Style (Optional)", avail_styles,
        index=avail_styles.index(st.session_state.selected_subcategory)
        if st.session_state.selected_subcategory in avail_styles else 0
    )
    st.session_state.selected_category    = sel_cat
    st.session_state.selected_subcategory = sel_sub
    if st.button("清除篩選" if lang == "中文" else "Clear Filters"):
        st.session_state.selected_category    = 'All'
        st.session_state.selected_subcategory = 'All'
        st.session_state.surprise_result      = []
        st.rerun()

# ── 食譜多選 ─────────────────────────────────────────────────────────────────
# 驚喜挑選的結果只在有效時才當 default，用完就清掉，不持續寫回 session_state
surprise = [r for r in st.session_state.surprise_result if r in recipe_options]
st.session_state.surprise_result = []  # 用完即清，避免持續影響

if recipe_options:
    selected = st.multiselect(
        "請選擇食譜（可輸入搜尋）" if lang == "中文" else "Select Recipe (type to search)",
        recipe_options,
        default=surprise,           # 只有驚喜挑選剛按完才有值，其他時候是 []
        key="recipe_multiselect"    # 固定 key，讓 Streamlit 原生管理選取狀態
    )
else:
    selected = []
    st.info("目前篩選條件下無可用食譜" if lang == "中文" else "No recipes available under current filters.")

# ── 食譜內容 ──────────────────────────────────────────────────────────────────
if selected:
    multipliers = {}
    for recipe in selected:
        rec_df_tmp = filtered_df[filtered_df["RecipeDisplay"] == recipe]
        if rec_df_tmp.empty:
            continue
        base_portion      = rec_df_tmp.iloc[0]["Portion"]
        recipe_id_for_key = rec_df_tmp["RecipeID"].iloc[0]
        mult = st.slider(
            f"{recipe} - {'份量倍率' if lang == '中文' else 'Multiplier'}",
            min_value=0.5, max_value=10.0, value=1.0, step=0.5,
            key=f"slider_{recipe_id_for_key}"
        )
        st.markdown(
            f"**{recipe} - {'單位份數' if lang == '中文' else 'Base Portion'}: "
            f"{base_portion} - {'份數' if lang == '中文' else 'Portion'}: {base_portion} x {mult}**"
        )
        multipliers[recipe] = mult

    selected_ids = filtered_df[filtered_df["RecipeDisplay"].isin(selected)]["RecipeID"].unique()

    for recipe in selected:
        rec_df = filtered_df[filtered_df["RecipeDisplay"] == recipe].copy()
        if rec_df.empty:
            continue
        recipe_id = rec_df["RecipeID"].iloc[0]
        mult      = multipliers.get(recipe, 1.0)
        image_url = rec_df["ImageURL"].iloc[0]

        # ── 圖片 ──
        if isinstance(image_url, str):
            if image_url.startswith("http"):
                st.markdown(
                    f'<img src="{image_url}" style="max-width:500px;max-height:700px;object-fit:contain;">',
                    unsafe_allow_html=True
                )
            else:
                image_path = Path(__file__).parent / image_url
                if image_path.exists():
                    st.image(str(image_path), width=500)
                else:
                    st.info("此食譜無圖片" if lang == "中文" else "No image for this recipe")
        else:
            st.info("此食譜無圖片" if lang == "中文" else "No image for this recipe")

        # ── 基本資訊 ──
        info = rec_df.iloc[0][["Portion", "Method"]]
        recipe_steps      = steps_df[steps_df["RecipeID"] == recipe_id]
        total_recipe_time = (
            recipe_steps[recipe_steps["Parallel"] == False]["CycleTime"].sum()
            if 'Parallel' in recipe_steps.columns and 'CycleTime' in recipe_steps.columns else 0
        )
        if lang == "中文":
            st.markdown(f"### 🍽️ {recipe} - 👥 份量：{info['Portion']} x{mult}")
            st.markdown(f"🍳 做法：{info['Method']}")
            st.markdown(f"⏱️ 預估時間：{total_recipe_time} 分鐘")
        else:
            st.markdown(f"### 🍽️ {recipe} - 👥 Portion: {info['Portion']} x{mult}")
            st.markdown(f"🍳 Method: {info['Method']}")
            st.markdown(f"⏱️ Estimated Time: {total_recipe_time} min")

        # ── 工具清單 ──
        st.subheader("🧰 工具清單" if lang == "中文" else "🧰 Tool List")
        recipe_tools = tools_df[tools_df["RecipeID"] == recipe_id]
        if recipe_tools.empty:
            st.info("工具資料待補" if lang == "中文" else "Tool data to be added")
        else:
            name_col  = "ToolName_zh" if lang == "中文" else "ToolName"
            opt_label = "非必要"      if lang == "中文" else "Optional"
            tool_disp = recipe_tools[[name_col]].copy()
            tool_disp.columns = ["工具" if lang == "中文" else "Tool"]
            tool_disp[opt_label] = (
                recipe_tools["Optional"].apply(lambda x: "✓" if x else "")
                if "Optional" in recipe_tools.columns else ""
            )
            st.table(tool_disp.reset_index(drop=True))

        # ── BoM 物料表 ──
        st.subheader("🫜 BoM 物料表" if lang == "中文" else "🫜 BoM (Bill of Materials)")
        for comp in rec_df["ComponentName"].unique():
            comp_df      = rec_df[rec_df["ComponentName"] == comp].copy()
            comp_display = comp_df["ComponentName_zh"].iloc[0] if lang == "中文" else comp
            if lang == "中文":
                comp_df["食材"] = comp_df["Ingredient_zh"]
                display = comp_df.groupby(["食材", "Unit", "Optional"])["Amount"].sum().mul(mult).reset_index()
                display["數量"]   = display["Amount"].apply(format_quantity)
                display["非必要"] = display["Optional"].apply(lambda x: "✓" if x else "")
                display = display[["食材", "數量", "Unit", "非必要"]]
                display.columns = ["食材", "數量", "單位", "非必要"]
            else:
                display = comp_df.groupby(["Ingredient", "Unit", "Optional"])["Amount"].sum().mul(mult).reset_index()
                display["Quantity"] = display["Amount"].apply(format_quantity)
                display["Optional"] = display["Optional"].apply(lambda x: "✓" if x else "")
                display = display[["Ingredient", "Quantity", "Unit", "Optional"]]
            st.subheader(f"• {comp_display}")
            st.table(display.reset_index(drop=True))

        # ── 生產流程 ──
        st.subheader("📋 生產流程" if lang == "中文" else "📋 Sequence")
        step_data       = steps_df[steps_df["RecipeID"] == recipe_id]
        part_src        = "Part_zh"        if lang == "中文" else "Part"
        instruction_src = "Instruction_zh" if lang == "中文" else "Instruction_en"
        required_cols   = ["StepOrder", part_src, instruction_src]
        if step_data.empty or not all(c in step_data.columns for c in required_cols):
            st.info("步驟資料待補" if lang == "中文" else "Step data to be added")
        else:
            extra = (["CycleTime", "Parallel"]
                     if "CycleTime" in step_data.columns and "Parallel" in step_data.columns else [])
            step_data = step_data[required_cols + extra].rename(columns={
                "StepOrder":     "步驟" if lang == "中文" else "Step",
                part_src:        "部位" if lang == "中文" else "Part",
                instruction_src: "說明" if lang == "中文" else "Instruction",
                "CycleTime":     "時間" if lang == "中文" else "CycleTime",
                "Parallel":      "並行" if lang == "中文" else "Parallel",
            })
            instr_col = "說明" if lang == "中文" else "Instruction"
            part_col  = "部位" if lang == "中文" else "Part"
            par_col   = "並行" if lang == "中文" else "Parallel"
            step_data[instr_col] = step_data[instr_col].apply(
                lambda x: str(x).replace('\n', '<br>').replace('; ', '<br>') if pd.notnull(x) else x
            )
            sequence_data, last_part = [], None
            for _, row in step_data.iterrows():
                cur = row[part_col]
                if cur != last_part:
                    sequence_data.append(row); last_part = cur
                else:
                    r = row.copy(); r[part_col] = ""; sequence_data.append(r)
            sequence_df = pd.DataFrame(sequence_data)
            if par_col in sequence_df.columns:
                sequence_df[par_col] = sequence_df[par_col].apply(lambda x: "✓" if x else "")
            st.markdown(sequence_df.to_html(escape=False, index=False), unsafe_allow_html=True)

    # ── 採購清單 ─────────────────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("📝 採購清單" if lang == "中文" else "📝 Procurement")
    all_df = filtered_df[filtered_df["RecipeDisplay"].isin(selected)].copy()
    all_df["Multiplier"]  = all_df["RecipeDisplay"].map(multipliers)
    all_df["TotalAmount"] = all_df["Amount"] * all_df["Multiplier"]
    if lang == "中文":
        all_df["食材"] = all_df["Ingredient_zh"]
        summary = all_df.groupby(["食材", "Unit", "Optional"])["TotalAmount"].sum().reset_index()
        summary["數量"]   = summary["TotalAmount"].apply(format_quantity)
        summary["非必要"] = summary["Optional"].apply(lambda x: "✓" if x else "")
        ingredient_lines = [
            f"{r['食材']}: {r['數量']}{r['Unit']}" + (" (非必要)" if r['非必要'] else "")
            for _, r in summary.iterrows()
        ]
    else:
        summary = all_df.groupby(["Ingredient", "Unit", "Optional"])["TotalAmount"].sum().reset_index()
        summary["Quantity"] = summary["TotalAmount"].apply(format_quantity)
        summary["Optional"] = summary["Optional"].apply(lambda x: "✓" if x else "")
        ingredient_lines = [
            f"{r['Ingredient']}: {r['Quantity']}{r['Unit']}" + (" (optional)" if r['Optional'] else "")
            for _, r in summary.iterrows()
        ]

    all_tools  = tools_df[tools_df["RecipeID"].isin(selected_ids)].copy()
    tool_lines = []
    if not all_tools.empty:
        if lang == "中文":
            ts = all_tools.groupby(["ToolName_zh", "Optional"]).size().reset_index(name="Count")
            ts["非必要"] = ts["Optional"].apply(lambda x: "✓" if x else "")
            tool_lines = [f"{r['ToolName_zh']}" + (" (非必要)" if r['非必要'] else "") for _, r in ts.iterrows()]
        else:
            ts = all_tools.groupby(["ToolName", "Optional"]).size().reset_index(name="Count")
            ts["Opt"] = ts["Optional"].apply(lambda x: "(optional)" if x else "")
            tool_lines = [f"{r['ToolName']}" + (f" {r['Opt']}" if r['Opt'] else "") for _, r in ts.iterrows()]

    st.markdown(
        f'<span style="margin-right:5px;">•</span>'
        f'<span style="font-size:1rem;font-weight:bold;">{"食材總和" if lang == "中文" else "Ingredients Summary"}</span>',
        unsafe_allow_html=True
    )
    st.code("\n".join(ingredient_lines))
    st.markdown(
        f'<span style="margin-right:5px;">•</span>'
        f'<span style="font-size:1rem;font-weight:bold;">{"工具總和" if lang == "中文" else "Tools Summary"}</span>',
        unsafe_allow_html=True
    )
    if tool_lines:
        st.code("\n".join(tool_lines))
    else:
        st.info("工具資料待補" if lang == "中文" else "Tool data to be added")

    st.markdown("---")
    st.markdown("### ⏱️ 預估總時間" if lang == "中文" else "### ⏱️ Estimated Total Time")
    total_time = 0
    for rid in selected_ids:
        rs = steps_df[steps_df["RecipeID"] == rid]
        if 'Parallel' in rs.columns and 'CycleTime' in rs.columns:
            total_time += rs[rs["Parallel"] == False]["CycleTime"].sum()
    st.markdown(f"{total_time} {'分鐘' if lang == '中文' else 'min'}")

else:
    st.info("請選擇至少一道食譜" if lang == "中文" else "Please select at least one recipe.")