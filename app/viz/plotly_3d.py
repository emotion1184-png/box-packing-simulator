# app/viz/plotly_3d.py
"""
개선된 3D 시각화 (사이즈 레이블 포함)
"""
import plotly.graph_objects as go
from core.models import PackingResult
import numpy as np

def create_3d_visualization(result: PackingResult, show_labels: bool = True) -> go.Figure:
    """
    3D 박스 적치 시각화
    - 포장박스: wireframe
    - 제품박스: 반투명 Mesh3d
    - 사이즈 레이블 표시
    """
    eff_L, eff_W, eff_H = result.effective_dimension
    
    fig = go.Figure()
    
    # 포장박스 테두리 (wireframe) - 더 굵게
    edges = [
        [(0,0,0), (eff_L,0,0)],
        [(0,0,0), (0,eff_W,0)],
        [(0,0,0), (0,0,eff_H)],
        [(eff_L,0,0), (eff_L,eff_W,0)],
        [(eff_L,0,0), (eff_L,0,eff_H)],
        [(0,eff_W,0), (eff_L,eff_W,0)],
        [(0,eff_W,0), (0,eff_W,eff_H)],
        [(0,0,eff_H), (eff_L,0,eff_H)],
        [(0,0,eff_H), (0,eff_W,eff_H)],
        [(eff_L,eff_W,0), (eff_L,eff_W,eff_H)],
        [(eff_L,0,eff_H), (eff_L,eff_W,eff_H)],
        [(0,eff_W,eff_H), (eff_L,eff_W,eff_H)],
    ]
    
    for edge in edges:
        x = [edge[0][0], edge[1][0]]
        y = [edge[0][1], edge[1][1]]
        z = [edge[0][2], edge[1][2]]
        fig.add_trace(go.Scatter3d(
            x=x, y=y, z=z,
            mode='lines',
            line=dict(color='black', width=5),
            showlegend=False,
            hoverinfo='skip'
        ))
    
    # 제품박스들
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f']
    sku_color_map = {}
    color_idx = 0
    
    for item in result.fitted_items:
        if item.sku not in sku_color_map:
            sku_color_map[item.sku] = colors[color_idx % len(colors)]
            color_idx += 1
        
        color = sku_color_map[item.sku]
        x0, y0, z0 = item.position
        l, w, h = item.dimension
        
        # 큐보이드 vertices
        vertices = np.array([
            [x0, y0, z0],
            [x0+l, y0, z0],
            [x0+l, y0+w, z0],
            [x0, y0+w, z0],
            [x0, y0, z0+h],
            [x0+l, y0, z0+h],
            [x0+l, y0+w, z0+h],
            [x0, y0+w, z0+h],
        ])
        
        # Mesh3d faces
        i = [0,0,0,0,1,1,2,2,4,4,3,3]
        j = [1,2,3,4,2,5,3,6,5,7,7,4]
        k = [2,3,4,5,5,6,6,7,7,6,4,7]
        
        hover_text = (f"<b>{item.name}</b><br>"
                     f"SKU: {item.sku}<br>"
                     f"Size: {l:.0f} × {w:.0f} × {h:.0f} mm<br>"
                     f"Position: ({x0:.0f}, {y0:.0f}, {z0:.0f})<br>"
                     f"Volume: {l*w*h:,.0f} mm³")
        
        fig.add_trace(go.Mesh3d(
            x=vertices[:,0],
            y=vertices[:,1],
            z=vertices[:,2],
            i=i, j=j, k=k,
            color=color,
            opacity=0.7,
            name=f"{item.sku}",
            text=hover_text,
            hoverinfo='text',
            showlegend=True
        ))
        
        # 사이즈 레이블 추가 (박스 중심에)
        if show_labels:
            center_x = x0 + l/2
            center_y = y0 + w/2
            center_z = z0 + h/2
            
            label_text = f"{l:.0f}×{w:.0f}×{h:.0f}"
            
            fig.add_trace(go.Scatter3d(
                x=[center_x],
                y=[center_y],
                z=[center_z],
                mode='text',
                text=[label_text],
                textposition='middle center',
                textfont=dict(size=10, color='white', family='Arial Black'),
                showlegend=False,
                hoverinfo='skip'
            ))
    
    # 레이아웃
    fig.update_layout(
        scene=dict(
            xaxis=dict(
                title='L (mm)', 
                range=[0, eff_L*1.1],
                showgrid=True,
                gridcolor='lightgray'
            ),
            yaxis=dict(
                title='W (mm)', 
                range=[0, eff_W*1.1],
                showgrid=True,
                gridcolor='lightgray'
            ),
            zaxis=dict(
                title='H (mm)', 
                range=[0, eff_H*1.1],
                showgrid=True,
                gridcolor='lightgray'
            ),
            aspectmode='data',
            camera=dict(
                eye=dict(x=1.5, y=1.5, z=1.2)
            )
        ),
        title=dict(
            text=f"3D Packing View - {result.pack_box_name}<br><sub>Fill Efficiency: {result.fill_ratio*100:.1f}%</sub>",
            x=0.5,
            xanchor='center'
        ),
        height=800,
        showlegend=True,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01
        )
    )
    
    return fig
