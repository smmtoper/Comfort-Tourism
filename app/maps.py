import plotly.graph_objects as go
import json


def create_choropleth(geojson, locations, z_values, index_type, zoom=5.3, center_lat=57.0, center_lon=105.0):
    if index_type == 'tci':
        colorscale = 'RdYlGn'
        zmin, zmax = 0, 100
        colorbar_title = "TCI (баллы)"
        hover_template = '<b>%{location}</b><br>TCI: %{z:.1f}<br>👆 Нажмите для подробностей<extra></extra>'
    else:
        colorscale = 'RdYlBu_r'
        zmin, zmax = -40, 50
        colorbar_title = "UTCI (°C)"
        hover_template = '<b>%{location}</b><br>UTCI: %{z:.1f}°C<br>👆 Нажмите для подробностей<extra></extra>'

    fig = go.Figure(go.Choroplethmapbox(
        geojson=geojson,
        locations=locations,
        z=z_values,
        colorscale=colorscale,
        zmin=zmin,
        zmax=zmax,
        marker_opacity=0.85,
        marker_line_width=0.5,
        marker_line_color='black',
        colorbar_title=colorbar_title,
        hovertemplate=hover_template,
        featureidkey="properties.name"
    ))

    fig.update_layout(
        mapbox_style="carto-positron",
        mapbox_zoom=zoom,
        mapbox_center={"lat": center_lat, "lon": center_lon},
        height=550,
        margin={"r": 0, "t": 0, "l": 0, "b": 0}
    )

    return json.loads(fig.to_json())


def create_tourism_choropleth(geojson, locations, z_values, zoom=5.3, center_lat=57.0, center_lon=105.0):
    """Создает карту для туристического потенциала"""

    colorscale = [
        [0.0, '#e74c3c'],  # 0-20: Сложная территория
        [0.2, '#e67e22'],
        [0.4, '#f39c12'],  # 20-40: Спящий гигант
        [0.6, '#3498db'],  # 40-60: Устойчивый туризм
        [0.8, '#2ecc71'],  # 60-80: Эталонная
        [1.0, '#27ae60']  # 80-100: Эталонная (высшая)
    ]

    fig = go.Figure(go.Choroplethmapbox(
        geojson=geojson,
        locations=locations,
        z=z_values,
        colorscale=colorscale,
        zmin=0,
        zmax=100,
        marker_opacity=0.85,
        marker_line_width=0.5,
        marker_line_color='black',
        colorbar_title="Туристический потенциал (баллы)",
        hovertemplate='<b>%{location}</b><br>Потенциал: %{z:.1f}<br>👆 Нажмите для подробностей<extra></extra>',
        featureidkey="properties.name"
    ))

    fig.update_layout(
        mapbox_style="carto-positron",
        mapbox_zoom=zoom,
        mapbox_center={"lat": center_lat, "lon": center_lon},
        height=550,
        margin={"r": 0, "t": 0, "l": 0, "b": 0}
    )

    return json.loads(fig.to_json())



