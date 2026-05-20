from flask import Blueprint, render_template, request, jsonify
from app.models import ClimateData
from app.maps import create_choropleth
import traceback

bp = Blueprint('main', __name__)

climate_data = None


def init_data(csv_path, geojson_path, tci_raster_path, utci_raster_path, sights_path):
    global climate_data
    climate_data = ClimateData(csv_path, geojson_path, tci_raster_path, utci_raster_path, sights_path)


@bp.route('/')
def index():
    return render_template('index.html', mo_list=climate_data.mo_list if climate_data else [])


@bp.route('/api/map_data')
def map_data():
    try:
        mode = request.args.get('mode', 'actual')
        index_type = request.args.get('index', 'tci')
        month = request.args.get('month', '07')

        print(f"📊 Запрос: mode={mode}, index={index_type}, month={month}")

        if mode == 'actual':
            date_input = request.args.get('date')
            if date_input is None:
                return jsonify({'figData': None, 'districtsData': {}})
            row = climate_data.get_data_by_date(date_input)
        elif mode == 'period':
            years_back = int(request.args.get('years_back', 5))
            row = climate_data.get_data_by_period(years_back, month)
        elif mode == 'avg':
            row = climate_data.get_avg_by_month(month)
        else:
            return jsonify({'figData': None, 'districtsData': {}})

        if row is None:
            print("⚠️ Данные не найдены")
            return jsonify({'figData': None, 'districtsData': {}})

        locations, z_values, districts_data = climate_data.get_district_values(row, index_type)

        if len(locations) == 0:
            return jsonify({'figData': None, 'districtsData': {}})

        fig_json = create_choropleth(climate_data.geojson, locations, z_values, index_type)

        return jsonify({
            'figData': fig_json,
            'districtsData': districts_data
        })

    except Exception as e:
        print(f"Ошибка в map_data: {e}")
        traceback.print_exc()
        return jsonify({'figData': None, 'districtsData': {}})


@bp.route('/api/district_history')
def district_history():
    mo = request.args.get('mo', '').strip()
    return jsonify(climate_data.get_district_history(mo))


@bp.route('/api/years')
def get_years():
    return jsonify(climate_data.get_available_years())


@bp.route('/api/district_raster')
def district_raster():
    mo = request.args.get('mo', '').strip()
    date = request.args.get('date', '').strip()
    index_type = request.args.get('index', 'tci')
    mode = request.args.get('mode', 'actual')
    years_back = request.args.get('years_back', '5')

    if mode == 'period':
        years_back = int(years_back)
        points = climate_data.get_raster_points_by_period(mo, years_back, index_type)
    else:
        points = climate_data.get_raster_points_by_district(mo, date, index_type)

    return jsonify(points)


@bp.route('/api/district_raster_stats')
def district_raster_stats():
    mo = request.args.get('mo', '').strip()
    date = request.args.get('date', '').strip()
    index_type = request.args.get('index', 'tci')
    mode = request.args.get('mode', 'actual')
    years_back = request.args.get('years_back', '5')

    if mode == 'period':
        years_back = int(years_back)
        stats = climate_data.get_raster_stats_by_period(mo, years_back, index_type)
    else:
        stats = climate_data.get_raster_stats_by_district(mo, date, index_type)

    return jsonify(stats)


@bp.route('/api/geojson_boundary')
def geojson_boundary():
    mo = request.args.get('mo', '').strip()

    if climate_data is None:
        return jsonify({'type': 'FeatureCollection', 'features': []})

    for feature in climate_data.geojson['features']:
        if feature['properties'].get('name') == mo:
            return jsonify({
                'type': 'FeatureCollection',
                'features': [feature]
            })

    return jsonify({'type': 'FeatureCollection', 'features': []})


@bp.route('/api/geojson')
def geojson():
    if climate_data is None:
        return jsonify({'type': 'FeatureCollection', 'features': []})
    return jsonify(climate_data.geojson)


# === МАРШРУТЫ ДЛЯ ТУРИСТИЧЕСКОЙ ВКЛАДКИ ===

@bp.route('/api/tourism_sights_all')
def tourism_sights_all():
    category = request.args.get('category', 'Все')
    sights = climate_data.get_all_sights_by_category(category)
    return jsonify(sights)


@bp.route('/api/tourism_sights_by_district')
def tourism_sights_by_district():
    mo = request.args.get('mo', '').strip()
    category = request.args.get('category', 'Все')
    sights = climate_data.get_sights_by_district(mo, category)
    return jsonify(sights)


@bp.route('/api/tourism_quadrant')
def tourism_quadrant():
    month = request.args.get('month', '07')
    quadrants = climate_data.get_quadrant_analysis(month)
    return jsonify(quadrants)


@bp.route('/api/tourism_categories')
def tourism_categories():
    categories = climate_data.get_sights_categories()
    return jsonify(categories)


# === РЕКОМЕНДАЦИИ ===

@bp.route('/api/recommendations')
def recommendations():
    """Возвращает ТОП-5 районов по комфорту (TCI + UTCI)"""
    try:
        month = request.args.get('month', '07')
        period = request.args.get('period', '10')

        if period == 'avg':
            row = climate_data.get_avg_by_month(month)
            period_text = "средние многолетние"
        else:
            years_back = int(period)
            row = climate_data.get_data_by_period(years_back, month)
            period_text = f"последние {years_back} лет"

        if row is None:
            return jsonify([])

        locations, z_values, districts_data = climate_data.get_district_values(row, 'tci')

        sights_count_dict = {}
        if climate_data.tourism_analyzer:
            sights_count_dict = climate_data.tourism_analyzer.sights_count

        recommendations = []
        for mo in locations:
            tci_val = districts_data[mo]['tci']
            utci_val = districts_data[mo]['utci']

            if tci_val is None:
                continue

            utci_norm = 45
            if utci_val is not None:
                utci_norm = max(0, min(90, (utci_val + 40) * 90 / 90))

            sights_count = sights_count_dict.get(mo, 0)
            rating = tci_val * 0.6 + utci_norm * 0.3 + min(sights_count, 50) * 0.2

            recommendations.append({
                'mo': mo,
                'tci': round(tci_val, 1),
                'utci': round(utci_val, 1) if utci_val is not None else None,
                'rating': round(rating, 1),
                'sights_count': sights_count,
                'period': period_text,
                'month': month
            })

        recommendations.sort(key=lambda x: x['rating'], reverse=True)
        return jsonify(recommendations[:5])

    except Exception as e:
        print(f"Ошибка в рекомендациях: {e}")
        traceback.print_exc()
        return jsonify([])

@bp.route('/api/district_raster_grid')
def district_raster_grid():
    mo = request.args.get('mo', '').strip()
    date = request.args.get('date', '').strip()
    index_type = request.args.get('index', 'tci')
    mode = request.args.get('mode', 'actual')
    years_back = request.args.get('years_back', '5')
    grid_size = float(request.args.get('grid_size', '0.05'))

    if mode == 'period':
        years_back = int(years_back)
        # Для периода пока оставляем как есть
        points = climate_data.get_raster_points_by_period(mo, years_back, index_type)
        return jsonify(points)
    else:
        grid_data = climate_data.get_raster_grid_by_district(mo, date, index_type, grid_size)
        return jsonify(grid_data)

@bp.route('/api/recommendations_seasonal')
def recommendations_seasonal():
    """Возвращает ТОП-5 районов с учётом сезонности"""
    try:
        month = request.args.get('month', '07')
        period = request.args.get('period', '10')
        season_type = request.args.get('season_type', 'comfort')

        if period == 'avg':
            row = climate_data.get_avg_by_month(month)
            period_text = "средние многолетние"
        else:
            years_back = int(period)
            row = climate_data.get_data_by_period(years_back, month)
            period_text = f"последние {years_back} лет"

        if row is None:
            return jsonify([])

        locations, z_values, districts_data = climate_data.get_district_values(row, 'tci')

        if climate_data.tourism_analyzer is None:
            return jsonify([])

        recommendations = []
        for mo in locations:
            tci_val = districts_data[mo]['tci']
            utci_val = districts_data[mo]['utci']

            if tci_val is None:
                continue

            utci_norm = 45
            if utci_val is not None:
                utci_norm = max(0, min(90, (utci_val + 40) * 90 / 90))

            climate_score = tci_val * 0.7 + utci_norm * 0.3

            if season_type == 'winter':
                season_count = climate_data.tourism_analyzer.get_sights_count_by_season(mo, 'winter')
                rating = climate_score * 0.7 + min(season_count, 30) * 0.3
                season_name = "❄️ Зимний отдых"
            elif season_type == 'summer':
                season_count = climate_data.tourism_analyzer.get_sights_count_by_season(mo, 'summer')
                rating = climate_score * 0.7 + min(season_count, 30) * 0.3
                season_name = "☀️ Летний отдых"
            elif season_type == 'year':
                season_count = climate_data.tourism_analyzer.get_sights_count_by_season(mo, 'year')
                rating = climate_score * 0.5 + min(season_count, 50) * 0.5
                season_name = "🏛️ Круглогодичный"
            else:
                season_count = climate_data.tourism_analyzer.sights_count.get(mo, 0)
                rating = climate_score
                season_name = "🌡️ Комфортный климат"

            recommendations.append({
                'mo': mo,
                'tci': round(tci_val, 1),
                'utci': round(utci_val, 1) if utci_val is not None else None,
                'rating': round(rating, 1),
                'sights_count': season_count,
                'season_type': season_type,
                'season_name': season_name,
                'period': period_text,
                'month': month
            })

        recommendations.sort(key=lambda x: x['rating'], reverse=True)
        return jsonify(recommendations[:5])

    except Exception as e:
        print(f"Ошибка в сезонных рекомендациях: {e}")
        traceback.print_exc()
        return jsonify([])