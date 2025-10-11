import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from controller.database.database import SessionLocal, Budget, SavingGoal, Transaction, Conversation
import numpy as np

# ============================================================================
# PAGE CONFIGURATION & THEMING
# ============================================================================

st.set_page_config(
    page_title="Personal Finance Advisor",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Detect if dark mode is enabled
is_dark_mode = st.get_option("theme.base") == "dark"

# Theme colors - customize these or they'll use defaults
PRIMARY_COLOR = "#4D94FF"  # Can be customized in .streamlit/config.toml
ACCENT_COLOR = "#4CAF50"
WARNING_COLOR = "#FFC107"
DANGER_COLOR = "#F44336"
SUCCESS_COLOR = "#4CAF50"

# Plotly template based on theme
PLOTLY_TEMPLATE = "plotly_dark" if is_dark_mode else "plotly_white"


# ============================================================================
# DATABASE FUNCTIONS
# ============================================================================

def get_user_id():
    """Get current user ID from Streamlit auth or session state."""
    if hasattr(st, 'user') and hasattr(st.user, 'sub'):
        return st.user.sub
    return st.session_state.get('user_id', 'demo_user')


def fetch_budgets(db: Session, user_id: str) -> pd.DataFrame:
    """Fetch all budgets for current user and calculate current_spent from transactions."""
    budgets = db.query(Budget).filter(Budget.user_id == user_id).all()
    if not budgets:
        return pd.DataFrame()
    
    data = []
    for b in budgets:
        # Calculate current_spent from actual transactions
        expenses = db.query(Transaction).filter(
            Transaction.user_id == user_id,
            Transaction.category == b.category,
            Transaction.type == "Expense"
        ).all()
        
        current_spent = sum(t.amount for t in expenses)
        
        data.append({
            'Budget ID': b.budget_id,
            'Category': b.category,
            'Monthly Limit': b.monthly_limit,
            'Current Spent': current_spent,
            'Remaining': b.monthly_limit - current_spent,
            'Progress %': (current_spent / b.monthly_limit * 100) if b.monthly_limit > 0 else 0,
            'Start Date': b.start_date
        })
    
    return pd.DataFrame(data)


def fetch_saving_goals(db: Session, user_id: str) -> pd.DataFrame:
    """Fetch all saving goals for current user and calculate current_savings from net transactions (Income - Expenses)."""
    goals = db.query(SavingGoal).filter(SavingGoal.user_id == user_id).all()
    if not goals:
        return pd.DataFrame()
    
    # Calculate total income and expenses
    all_transactions = db.query(Transaction).filter(
        Transaction.user_id == user_id
    ).all()
    
    total_income = sum(t.amount for t in all_transactions if t.type == "Income")
    total_expenses = sum(t.amount for t in all_transactions if t.type == "Expense")
    net_savings = total_income - total_expenses
    
    data = []
    for g in goals:
        # Current savings is net (income - expenses)
        current_savings = max(0, net_savings)  # Don't go negative
        
        data.append({
            'Goal ID': g.id,
            'Goal Name': g.goal_name,
            'Target Amount': g.target_amount,
            'Current Savings': current_savings,
            'Remaining': max(0, g.target_amount - current_savings),
            'Progress %': (current_savings / g.target_amount * 100) if g.target_amount > 0 else 0,
            'Deadline': g.deadline,
            'Monthly Needed': g.monthly_savings_needed,
            'Weekly Needed': g.weekly_savings_needed,
            'Total Income': total_income,
            'Total Expenses': total_expenses,
            'Net Savings': net_savings
        })
    
    return pd.DataFrame(data)


def fetch_transactions(db: Session, user_id: str) -> pd.DataFrame:
    """Fetch all transactions for current user."""
    transactions = db.query(Transaction).filter(Transaction.user_id == user_id).all()
    if not transactions:
        return pd.DataFrame()
    
    data = [{
        'Transaction ID': t.transactions_id,
        'Date': t.date,
        'Type': t.type,
        'Category': t.category,
        'Amount': t.amount,
        'Description': t.user_request
    } for t in transactions]
    
    df = pd.DataFrame(data)
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values('Date', ascending=False)
    return df


# ============================================================================
# VISUALIZATION FUNCTIONS
# ============================================================================

def plot_budget_overview(df: pd.DataFrame) -> go.Figure:
    """Create budget vs actual spending visualization."""
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No budget data available", showarrow=False)
        return fig
    
    fig = go.Figure(data=[
        go.Bar(x=df['Category'], y=df['Monthly Limit'], name='Monthly Limit', 
               marker_color=PRIMARY_COLOR, opacity=0.7),
        go.Bar(x=df['Category'], y=df['Current Spent'], name='Current Spent',
               marker_color='#FF6B6B', opacity=0.9)
    ])
    
    fig.update_layout(
        title='Budget vs Actual Spending',
        barmode='group',
        hovermode='x unified',
        template=PLOTLY_TEMPLATE,
        height=400
    )
    return fig


def plot_budget_progress(df: pd.DataFrame) -> go.Figure:
    """Create budget progress gauge charts."""
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No budget data available", showarrow=False)
        return fig
    
    fig = go.Figure()
    
    for idx, row in df.iterrows():
        progress = min(row['Progress %'], 100)
        color = '#4CAF50' if progress < 70 else '#FFC107' if progress < 100 else '#F44336'
        
        # Calculate grid position (2 columns, multiple rows)
        col = idx % 2
        row_num = idx // 2
        
        # Domain must be between 0-1
        x_start = col * 0.48
        x_end = x_start + 0.45
        y_start = max(0, 1 - (row_num + 1) * 0.48)
        y_end = min(1, 1 - row_num * 0.48)
        
        fig.add_trace(go.Indicator(
            domain={'x': [x_start, x_end], 'y': [y_start, y_end]},
            value=progress,
            title={'text': row['Category']},
            mode='gauge+number',
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': color},
                'steps': [
                    {'range': [0, 50], 'color': '#E8F5E9'},
                    {'range': [50, 100], 'color': '#FFF3E0'}
                ],
                'threshold': {
                    'line': {'color': 'red', 'width': 4},
                    'thickness': 0.75,
                    'value': 100
                }
            }
        ))
    
    fig.update_layout(
        title='Budget Progress by Category (%)',
        template=PLOTLY_TEMPLATE,
        height=max(400, len(df) * 200)
    )
    return fig


def plot_saving_goals(df: pd.DataFrame) -> go.Figure:
    """Create saving goals progress visualization."""
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No saving goals available", showarrow=False)
        return fig
    
    fig = go.Figure(data=[
        go.Bar(x=df['Goal Name'], y=df['Current Savings'], name='Saved',
               marker_color=PRIMARY_COLOR),
        go.Bar(x=df['Goal Name'], y=df['Remaining'], name='Remaining',
               marker_color='#CCCCCC', opacity=0.5)
    ])
    
    fig.update_layout(
        title='Saving Goals Progress',
        barmode='stack',
        hovermode='x unified',
        template=PLOTLY_TEMPLATE,
        height=400
    )
    return fig


def plot_transactions(df: pd.DataFrame) -> go.Figure:
    """Create transaction analysis visualization."""
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No transactions available", showarrow=False)
        return fig
    
    # Category wise spending
    category_spend = df.groupby('Category')['Amount'].sum().sort_values(ascending=False)
    
    fig = px.pie(
        values=category_spend.values,
        names=category_spend.index,
        title='Spending by Category',
        template=PLOTLY_TEMPLATE,
        hole=0.3
    )
    
    fig.update_layout(height=400)
    return fig


def plot_transaction_timeline(df: pd.DataFrame) -> go.Figure:
    """Create transaction timeline visualization."""
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No transactions available", showarrow=False)
        return fig
    
    daily_data = df.groupby(df['Date'].dt.date)['Amount'].sum().reset_index()
    daily_data.columns = ['Date', 'Amount']
    
    fig = go.Figure(data=[
        go.Scatter(
            x=daily_data['Date'],
            y=daily_data['Amount'],
            mode='lines+markers',
            name='Daily Spending',
            line=dict(color=PRIMARY_COLOR, width=2),
            fill='tozeroy'
        )
    ])
    
    fig.update_layout(
        title='Daily Spending Trend',
        xaxis_title='Date',
        yaxis_title='Amount',
        template=PLOTLY_TEMPLATE,
        height=400,
        hovermode='x unified'
    )
    return fig


# ============================================================================
# MAIN APPLICATION
# ============================================================================

def main():
    user_id = get_user_id()
    db = SessionLocal()
    
    # Header
    st.markdown("# 💰 Personal Finance Advisor Dashboard")
    # st.markdown(f"**User ID:** {user_id}")
    st.divider()
    
    # Create tabs
    tab1, tab2, tab3 = st.tabs(["📊 Budget Planner", "🎯 Saving Goals", "💳 Transactions"])
    
    # ========================================================================
    # TAB 1: BUDGET PLANNER
    # ========================================================================
    with tab1:
        st.subheader("Budget Management")
        
        budget_df = fetch_budgets(db, user_id)
        
        if budget_df.empty:
            st.info("No budgets found. Create your first budget to get started!")
        else:
            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Budget", f"${budget_df['Monthly Limit'].sum():,.0f}")
            with col2:
                st.metric("Total Spent", f"${budget_df['Current Spent'].sum():,.0f}")
            with col3:
                st.metric("Total Remaining", f"${budget_df['Remaining'].sum():,.0f}")
            with col4:
                avg_progress = budget_df['Progress %'].mean()
                st.metric("Avg Progress", f"{avg_progress:.1f}%")
            
            st.divider()
            
            # Visualizations
            col1, col2 = st.columns(2)
            with col1:
                st.plotly_chart(plot_budget_overview(budget_df), use_container_width=True)
            with col2:
                st.plotly_chart(plot_budget_progress(budget_df), use_container_width=True)
            
            st.divider()
            st.subheader("Budget Details")
            
            # Interactive table with row selection
            if st.checkbox("Show detailed budget table"):
                display_df = budget_df.copy()
                display_df['Monthly Limit'] = display_df['Monthly Limit'].apply(lambda x: f"${x:,.0f}")
                display_df['Current Spent'] = display_df['Current Spent'].apply(lambda x: f"${x:,.0f}")
                display_df['Remaining'] = display_df['Remaining'].apply(lambda x: f"${x:,.0f}")
                display_df['Progress %'] = display_df['Progress %'].apply(lambda x: f"{x:.1f}%")
                
                st.dataframe(display_df, use_container_width=True, hide_index=True)
                
                # Row detail view
                selected_idx = st.selectbox(
                    "Select a budget to view details:",
                    options=range(len(budget_df)),
                    format_func=lambda x: f"{budget_df.iloc[x]['Category']} - {budget_df.iloc[x]['Progress %']:.1f}% used"
                )
                
                if selected_idx is not None:
                    selected_budget = budget_df.iloc[selected_idx]
                    st.subheader(f"Budget Details: {selected_budget['Category']}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        # Circular progress
                        fig = go.Figure(go.Indicator(
                            mode="gauge+number+delta",
                            value=selected_budget['Progress %'],
                            title={'text': "Budget Used %"},
                            delta={'reference': 100},
                            gauge={
                                'axis': {'range': [0, 100]},
                                'bar': {'color': "#4CAF50" if selected_budget['Progress %'] < 70 else "#FFC107" if selected_budget['Progress %'] < 100 else "#F44336"},
                                'steps': [
                                    {'range': [0, 70], 'color': '#E8F5E9'},
                                    {'range': [70, 100], 'color': '#FFF3E0'}
                                ]
                            }
                        ))
                        fig.update_layout(
                            template=PLOTLY_TEMPLATE,
                            height=300
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    
                    with col2:
                        st.metric("Category", selected_budget['Category'])
                        st.metric("Monthly Limit", f"${selected_budget['Monthly Limit']:,.0f}")
                        st.metric("Current Spent", f"${selected_budget['Current Spent']:,.0f}")
                        st.metric("Remaining", f"${selected_budget['Remaining']:,.0f}")
                        st.metric("Start Date", selected_budget['Start Date'])
    
    # ========================================================================
    # TAB 2: SAVING GOALS
    # ========================================================================
    with tab2:
        st.subheader("Saving Goals Tracker")
        
        goals_df = fetch_saving_goals(db, user_id)
        
        if goals_df.empty:
            st.info("No saving goals found. Create your first goal to get started!")
        else:
            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Target", f"${goals_df['Target Amount'].sum():,.0f}")
            with col2:
                st.metric("Total Saved", f"${goals_df['Current Savings'].sum():,.0f}")
            with col3:
                st.metric("Total Remaining", f"${goals_df['Remaining'].sum():,.0f}")
            with col4:
                avg_progress = goals_df['Progress %'].mean()
                st.metric("Avg Progress", f"{avg_progress:.1f}%")
            
            st.divider()
            
            # Visualization
            st.plotly_chart(plot_saving_goals(goals_df), use_container_width=True)
            
            st.divider()
            st.subheader("Saving Goals Details")
            
            if st.checkbox("Show detailed goals table"):
                display_goals_df = goals_df.copy()
                display_goals_df['Target Amount'] = display_goals_df['Target Amount'].apply(lambda x: f"${x:,.0f}")
                display_goals_df['Current Savings'] = display_goals_df['Current Savings'].apply(lambda x: f"${x:,.0f}")
                display_goals_df['Remaining'] = display_goals_df['Remaining'].apply(lambda x: f"${x:,.0f}")
                display_goals_df['Progress %'] = display_goals_df['Progress %'].apply(lambda x: f"{x:.1f}%")
                display_goals_df['Monthly Needed'] = display_goals_df['Monthly Needed'].apply(lambda x: f"${x:,.0f}")
                display_goals_df['Weekly Needed'] = display_goals_df['Weekly Needed'].apply(lambda x: f"${x:,.0f}")
                
                st.dataframe(display_goals_df, use_container_width=True, hide_index=True)
                
                # Row detail view
                selected_goal_idx = st.selectbox(
                    "Select a goal to view details:",
                    options=range(len(goals_df)),
                    format_func=lambda x: f"{goals_df.iloc[x]['Goal Name']} - {goals_df.iloc[x]['Progress %']:.1f}% complete"
                )
                
                if selected_goal_idx is not None:
                    selected_goal = goals_df.iloc[selected_goal_idx]
                    st.subheader(f"Goal Details: {selected_goal['Goal Name']}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        # Circular progress
                        fig = go.Figure(go.Indicator(
                            mode="gauge+number",
                            value=min(selected_goal['Progress %'], 100),
                            title={'text': "Goal Progress %"},
                            gauge={
                                'axis': {'range': [0, 100]},
                                'bar': {'color': PRIMARY_COLOR},
                                'steps': [
                                    {'range': [0, 50], 'color': '#E8F5E9'},
                                    {'range': [50, 100], 'color': '#FFF3E0'}
                                ]
                            }
                        ))
                        fig.update_layout(
                            template=PLOTLY_TEMPLATE,
                            height=300
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    
                    with col2:
                        st.metric("Goal Name", selected_goal['Goal Name'])
                        st.metric("Target Amount", f"${selected_goal['Target Amount']:,.0f}")
                        st.metric("Current Savings", f"${selected_goal['Current Savings']:,.0f}")
                        st.metric("Remaining", f"${selected_goal['Remaining']:,.0f}")
                        st.metric("Deadline", selected_goal['Deadline'])
                    
                    st.divider()
                    st.subheader("💡 Savings Tracking")
                    
                    # Transaction summary
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total Income", f"${selected_goal['Total Income']:,.0f}", delta="inflow")
                    with col2:
                        st.metric("Total Expenses", f"${selected_goal['Total Expenses']:,.0f}", delta="outflow", delta_color="inverse")
                    with col3:
                        st.metric("Net Savings", f"${selected_goal['Net Savings']:,.0f}")
                    
                    st.divider()
                    st.subheader("📊 Required Savings Rate")
                    
                    # Savings needed tracking
                    col1, col2 = st.columns(2)
                    with col1:
                        st.info(f"""
                        **Monthly Savings Needed:** ${selected_goal['Monthly Needed']:,.0f}
                        
                        To reach your goal by {selected_goal['Deadline']}, you need to save this amount every month.
                        """)
                    
                    with col2:
                        st.info(f"""
                        **Weekly Savings Needed:** ${selected_goal['Weekly Needed']:,.0f}
                        
                        Break it down to weekly savings targets to stay on track.
                        """)
                    
                    # Progress indicator
                    st.subheader("📈 Are You On Track?")
                    
                    monthly_progress = selected_goal['Net Savings'] / selected_goal['Monthly Needed'] * 100 if selected_goal['Monthly Needed'] > 0 else 0
                    
                    if monthly_progress >= 100:
                        st.success(f"✅ Exceeding target! You're {monthly_progress:.0f}% of monthly savings needed.")
                    elif monthly_progress >= 75:
                        st.warning(f"⚠️ On track! You're {monthly_progress:.0f}% of monthly savings needed.")
                    else:
                        st.error(f"❌ Below target. You're only {monthly_progress:.0f}% of monthly savings needed.")
    
    # ========================================================================
    # TAB 3: TRANSACTIONS
    # ========================================================================
    with tab3:
        st.subheader("Transaction History")
        
        transactions_df = fetch_transactions(db, user_id)
        
        if transactions_df.empty:
            st.info("No transactions found. Add your first transaction to get started!")
        else:
            # Summary metrics
            expenses = transactions_df[transactions_df['Type'] == 'Expense']['Amount'].sum()
            income = transactions_df[transactions_df['Type'] == 'Income']['Amount'].sum()
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Expenses", f"${expenses:,.0f}")
            with col2:
                st.metric("Total Income", f"${income:,.0f}")
            with col3:
                st.metric("Net Balance", f"${income - expenses:,.0f}", delta=f"${income - expenses:,.0f}")
            
            st.divider()
            
            # Visualizations
            col1, col2 = st.columns(2)
            with col1:
                st.plotly_chart(plot_transactions(transactions_df), use_container_width=True)
            with col2:
                st.plotly_chart(plot_transaction_timeline(transactions_df), use_container_width=True)
            
            st.divider()
            st.subheader("Transaction Details")
            
            # Filters
            col1, col2, col3 = st.columns(3)
            with col1:
                filter_type = st.multiselect(
                    "Filter by Type:",
                    options=transactions_df['Type'].unique(),
                    default=transactions_df['Type'].unique()
                )
            with col2:
                filter_category = st.multiselect(
                    "Filter by Category:",
                    options=transactions_df['Category'].unique(),
                    default=transactions_df['Category'].unique()
                )
            with col3:
                date_range = st.date_input(
                    "Date Range:",
                    value=(transactions_df['Date'].min().date(), transactions_df['Date'].max().date()),
                    key="date_range"
                )
            
            # Apply filters
            filtered_df = transactions_df[
                (transactions_df['Type'].isin(filter_type)) &
                (transactions_df['Category'].isin(filter_category)) &
                (transactions_df['Date'].dt.date >= date_range[0]) &
                (transactions_df['Date'].dt.date <= date_range[1])
            ]
            
            # Display transactions table
            display_trans_df = filtered_df.copy()
            display_trans_df['Date'] = display_trans_df['Date'].dt.strftime('%Y-%m-%d')
            display_trans_df['Amount'] = display_trans_df['Amount'].apply(lambda x: f"${x:,.0f}")
            
            st.dataframe(display_trans_df, use_container_width=True, hide_index=True)
            
            # Row detail view
            if len(filtered_df) > 0:
                selected_trans_idx = st.selectbox(
                    "Select a transaction to view details:",
                    options=range(len(filtered_df)),
                    format_func=lambda x: f"{filtered_df.iloc[x]['Date'].strftime('%Y-%m-%d')} - {filtered_df.iloc[x]['Category']} (${filtered_df.iloc[x]['Amount']:,.0f})"
                )
                
                if selected_trans_idx is not None:
                    selected_transaction = filtered_df.iloc[selected_trans_idx]
                    st.subheader("Transaction Details")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Date", selected_transaction['Date'].strftime('%Y-%m-%d'))
                        st.metric("Type", selected_transaction['Type'])
                    with col2:
                        st.metric("Category", selected_transaction['Category'])
                        st.metric("Amount", f"${selected_transaction['Amount']:,.0f}")
                    
                    st.text_area("Description", value=selected_transaction['Description'], disabled=True)
    
    db.close()


if __name__ == "__main__":
    main()