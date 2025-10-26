import streamlit as st
import pandas as pd
import plotly.express as px
import random
from food import df

# ------------------------------
# Page Config
# ------------------------------
st.set_page_config(
    page_title="Anti-Inflammatory Foods Dashboard",
    page_icon="🥗",
    layout="wide"
)

# ------------------------------
# Custom CSS for cards and styling
# ------------------------------
st.markdown("""
<style>
.card {
    background-color: #f0f2f6;
    padding: 15px;
    border-radius: 15px;
    box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
    text-align: center;
}
.card-title {
    font-size: 20px;
    font-weight: bold;
}
.card-value {
    font-size: 28px;
    font-weight: bold;
    color: #2E8B57;
}
</style>
""", unsafe_allow_html=True)

# ------------------------------
# Category Icons
# ------------------------------
category_icons = {
    'Carbohydrates': '🍞',
    'Proteins': '🍗',
    'Vegetables': '🥦',
    'Fruits': '🍎',
    'Nuts & Seeds': '🥜',
    'Spices & Herbs': '🌿'
}

# ------------------------------
# Sidebar Filters
# ------------------------------
st.sidebar.header("Filter Foods")
regions = sorted(df['Region'].dropna().unique())
categories = sorted(df['Category'].dropna().unique())
selected_regions = st.sidebar.multiselect("Select Region(s)", regions, default=regions)
selected_categories = st.sidebar.multiselect("Select Category(s)", categories, default=categories)
search_text = st.sidebar.text_input("Search Food or Notes")

# ------------------------------
# Filter Data
# ------------------------------
filtered_df = df[
    (df['Region'].isin(selected_regions)) &
    (df['Category'].isin(selected_categories)) &
    (df['Food'].str.contains(search_text, case=False, na=False) |
     df['Notes'].str.contains(search_text, case=False, na=False))
].copy()

# Add icon column
filtered_df['Icon'] = filtered_df['Category'].map(category_icons).fillna('🍽️')

# ------------------------------
# Tabs for layout
# ------------------------------
tab1, tab2, tab3 = st.tabs(["📋 Foods Table", "📊 Charts", "🥙 7-Day Meal Plan"])

# ------------------------------
# Tab 1: Foods Table + Metrics Cards
# ------------------------------
with tab1:
    st.title("🥗 Anti-Inflammatory Foods")

    col1, col2, col3 = st.columns(3)
    col1.markdown(f'<div class="card"><div class="card-title">Total Foods</div><div class="card-value">{len(df)}</div></div>', unsafe_allow_html=True)
    col2.markdown(f'<div class="card"><div class="card-title">Shown Foods</div><div class="card-value">{len(filtered_df)}</div></div>', unsafe_allow_html=True)
    avg_score = round(filtered_df['Anti_Inflam'].mean(),1) if len(filtered_df) else 0
    col3.markdown(f'<div class="card"><div class="card-title">Avg Anti-Inflam Score</div><div class="card-value">{avg_score}</div></div>', unsafe_allow_html=True)

    st.markdown("### 📋 Foods Table")
    table_df = filtered_df.sort_values('Food')[['Icon','Food','Category','Region','Anti_Inflam','Notes']]
    st.dataframe(
        table_df.style.format({"Anti_Inflam": "{:.1f}"})
        .set_properties(**{'text-align': 'left'})
    )

# ------------------------------
# Tab 2: Charts
# ------------------------------
with tab2:
    st.markdown("### 🌿 Top 10 Anti-Inflammatory Foods")
    top_foods = filtered_df.sort_values(by="Anti_Inflam", ascending=False).head(10)
    top_foods['Food'] = top_foods['Icon'] + ' ' + top_foods['Food']
    st.table(top_foods[['Food','Category','Region','Anti_Inflam','Notes']])

    st.markdown("### 📊 Foods Distribution by Region")
    region_df = filtered_df.groupby('Region').agg({
        'Food':'count',
        'Notes': lambda x: ', '.join(x)
    }).reset_index()
    fig_region = px.bar(
        region_df,
        x='Region', y='Food',
        hover_data={'Notes':True, 'Food':True},
        labels={'Food':'Number of Foods'},
        color='Food', color_continuous_scale='Viridis'
    )
    st.plotly_chart(fig_region, use_container_width=True)

    st.markdown("### 📊 Foods Distribution by Category")
    fig_cat = px.pie(
        filtered_df,
        names='Category',
        values='Anti_Inflam',
        hover_data={'Food':True,'Notes':True},
        title='Food Categories',
        color_discrete_sequence=px.colors.sequential.RdBu
    )
    st.plotly_chart(fig_cat, use_container_width=True)

# ------------------------------
# Tab 3: Meal Plan Generator
# ------------------------------
with tab3:
    st.markdown("### 🥙 Generate 7-Day Anti-Inflammatory Meal Plan")

    def generate_day_meal(lf):
        carbs = lf[lf['Category']=='Carbohydrates']['Food'].tolist()
        proteins = lf[lf['Category']=='Proteins']['Food'].tolist()
        vegs = lf[lf['Category']=='Vegetables']['Food'].tolist()
        fruits = lf[lf['Category']=='Fruits']['Food'].tolist()
        day = {
            'Breakfast': f"{category_icons.get('Carbohydrates','🍞')} {random.choice(carbs)} + {category_icons.get('Fruits','🍎')} {random.choice(fruits)}" if carbs and fruits else '',
            'Lunch': f"{category_icons.get('Carbohydrates','🍞')} {random.choice(carbs)} + {category_icons.get('Proteins','🍗')} {random.choice(proteins)} + {category_icons.get('Vegetables','🥦')} {random.choice(vegs)}" if carbs and proteins and vegs else '',
            'Dinner': f"{category_icons.get('Carbohydrates','🍞')} {random.choice(carbs)} + {category_icons.get('Proteins','🍗')} {random.choice(proteins)} + {category_icons.get('Vegetables','🥦')} {random.choice(vegs)}" if carbs and proteins and vegs else '',
            'Snack': f"{category_icons.get('Fruits','🍎')} {random.choice(fruits)}" if fruits else ''
        }
        return day

    if st.button("Generate 7-Day Plan"):
        plan = {}
        for i in range(7):
            day = pd.Timestamp.now().date() + pd.Timedelta(days=i)
            plan[str(day)] = generate_day_meal(filtered_df)
        
        st.markdown("### 🗓️ 7-Day Meal Plan")
        st.table(pd.DataFrame(plan).T)

        st.markdown("### 📈 Daily Avg Anti-Inflammatory Score")
        daily_scores = []
        for day_meals in plan.values():
            foods_list = ' + '.join([v.split(' ',1)[1] for v in day_meals.values() if v]).split(' + ')
            score_sum = filtered_df[filtered_df['Food'].isin(foods_list)]['Anti_Inflam'].sum()
            daily_scores.append(score_sum/len(foods_list) if foods_list else 0)
        st.line_chart(daily_scores)
