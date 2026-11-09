import plotly.express as px

PALETTE = ["#2a9d8f", "#264653", "#e9c46a", "#f4a261", "#e76f51"]


def brl(value):
    """Format a number as Brazilian reais, e.g. R$ 1,234,567"""
    return f"R$ {value:,.0f}"


def num(value):
    return f"{value:,.0f}"


def style(fig, height=380):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=50, b=10), template="plotly_white")
    return fig


def bar(df, x, y, title, horizontal=False, color=None):
    if horizontal:
        fig = px.bar(df.sort_values(x), x=x, y=y, orientation="h", title=title,
                     color_discrete_sequence=PALETTE)
    else:
        fig = px.bar(df, x=x, y=y, title=title, color=color, color_discrete_sequence=PALETTE)
    return style(fig)
    