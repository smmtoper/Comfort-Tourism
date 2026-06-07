import pandas as pd
import json
import xarray as xr
import numpy as np
from shapely.geometry import Point, shape
from app.tourism_analyzer import TourismAnalyzer


class ClimateData:
    def __init__(self, csv_path, geojson_path, tci_raster_path=None, utci_raster_path=None, sights_path=None):
        self.df = pd.read_csv(csv_path)
        self.df['time'] = self.df['time'].astype(str)

        with open(geojson_path, 'r', encoding='utf-8') as f:
            self.geojson = json.load(f)

        self.mo_list = [feature['properties'].get('name') for feature in self.geojson['features']]

        self.tci_raster = None
        if tci_raster_path:
            try:
                self.tci_raster = xr.open_dataset(tci_raster_path)
                print(f"✅ Растр TCI загружен: {self.tci_raster.sizes}")
            except Exception as e:
                print(f"⚠️ Ошибка загрузки TCI растра: {e}")

        self.utci_raster = None
        if utci_raster_path:
            try:
                self.utci_raster = xr.open_dataset(utci_raster_path)
                print(f"✅ Растр UTCI загружен: {self.utci_raster.sizes}")
            except Exception as e:
                print(f"⚠️ Ошибка загрузки UTCI растра: {e}")

        self.sights_df = None
        self.tourism_analyzer = None
        if sights_path:
            try:
                self.sights_df = pd.read_csv(sights_path, encoding='utf-16-le', sep='\t')
                print(f"✅ Достопримечательности загружены: {len(self.sights_df)} объектов")
                self.tourism_analyzer = TourismAnalyzer(self.df, self.sights_df, self.mo_list)
            except Exception as e:
                print(f"⚠️ Ошибка загрузки достопримечательностей: {e}")

        print(f"✅ Загружено: {len(self.df)} дат, {len(self.mo_list)} районов")

    def get_raster_grid_by_district(self, mo_name, date_input, index_type='tci', grid_size=0.05):
        """
        Возвращает сетку (grid) для района.
        grid_size — размер ячейки в градусах (0.05 ≈ 5 км)
        """
        if index_type == 'tci':
            if self.tci_raster is None:
                return []
            raster_ds = self.tci_raster
            value_name = 'TCI'
        else:
            if self.utci_raster is None:
                return []
            raster_ds = self.utci_raster
            value_name = 'UTCI'

        try:
            # Находим индекс времени
            time_idx = None
            for i, t in enumerate(raster_ds.time.values):
                t_str = str(t)[:7]
                if t_str == date_input:
                    time_idx = i
                    break

            if time_idx is None:
                return []

            data_2d = raster_ds[value_name].isel(time=time_idx)

            # Получаем полигон района
            polygon = None
            for feature in self.geojson['features']:
                if feature['properties'].get('name') == mo_name:
                    polygon = shape(feature['geometry'])
                    break

            if polygon is None:
                return []

            # Собираем все точки с координатами и значениями
            points = []
            lats = data_2d.latitude.values
            lons = data_2d.longitude.values

            for i, lat in enumerate(lats):
                for j, lon in enumerate(lons):
                    point = Point(lon, lat)
                    if polygon.contains(point):
                        val = data_2d.values[i, j]
                        if not np.isnan(val):
                            points.append({
                                'lat': float(lat),
                                'lon': float(lon),
                                'value': float(val)
                            })

            if not points:
                return []

            # Группируем в сетку (grid)
            grid_cells = {}
            for p in points:
                # Округляем координаты до размера ячейки
                cell_x = round(p['lon'] / grid_size) * grid_size
                cell_y = round(p['lat'] / grid_size) * grid_size
                cell_key = f"{cell_x},{cell_y}"

                if cell_key not in grid_cells:
                    grid_cells[cell_key] = {
                        'lon': cell_x,
                        'lat': cell_y,
                        'values': []
                    }
                grid_cells[cell_key]['values'].append(p['value'])

            # Формируем результат: центр ячейки и среднее значение
            result = []
            for cell_key, cell_data in grid_cells.items():
                result.append({
                    'lon': cell_data['lon'] + grid_size / 2,
                    'lat': cell_data['lat'] + grid_size / 2,
                    'value': sum(cell_data['values']) / len(cell_data['values']),
                    'count': len(cell_data['values'])
                })

            return result

        except Exception as e:
            print(f"Ошибка получения сетки: {e}")
            return []


    def get_data_by_date(self, date_input):

        matching_rows = self.df[self.df['time'].str.startswith(date_input)]
        return matching_rows.iloc[0] if not matching_rows.empty else None

    def get_avg_by_month(self, month):
        month_pattern = f'-{month}-'
        month_rows = self.df[self.df['time'].str.contains(month_pattern)]
        if month_rows.empty:
            return None
        avg_row = month_rows.mean(numeric_only=True)
        avg_row['time'] = f"avg-{month}"
        return avg_row

    def get_district_values(self, row, index_type='tci'):
        locations = []
        z_values = []
        districts_data = {}

        for mo in self.mo_list:
            tci_col = f'{mo}_tci'
            utci_col = f'{mo}_utci'

            has_tci = tci_col in self.df.columns

            if not has_tci:
                continue

            tci_val = row[tci_col] if row is not None else None
            utci_val = row[utci_col] if utci_col in self.df.columns and row is not None else None

            if tci_val is None or pd.isna(tci_val):
                continue

            locations.append(mo)
            districts_data[mo] = {
                'tci': float(tci_val),
                'utci': float(utci_val) if utci_val is not None and pd.notna(utci_val) else None
            }

            if index_type == 'tci':
                z_values.append(float(tci_val))
            else:
                if utci_val is not None and pd.notna(utci_val):
                    z_values.append(float(utci_val))

        return locations, z_values, districts_data

    def get_district_history(self, mo):
        tci_col = f'{mo}_tci'
        utci_col = f'{mo}_utci'

        if tci_col not in self.df.columns:
            return []

        result = []
        for _, row in self.df.iterrows():
            tci_val = row[tci_col]
            utci_val = row[utci_col] if utci_col in self.df.columns else None

            result.append({
                'date': row['time'],
                'tci': float(tci_val) if pd.notna(tci_val) else None,
                'utci': float(utci_val) if utci_val is not None and pd.notna(utci_val) else None
            })
        return result

    def get_available_years(self):
        years = sorted(self.df['time'].str[:4].unique())
        return [int(y) for y in years if y.isdigit()]

    def get_raster_points_by_district(self, mo_name, date_input, index_type='tci'):
        if index_type == 'tci':
            if self.tci_raster is None:
                return []
            raster_ds = self.tci_raster
            value_name = 'TCI'
        else:
            if self.utci_raster is None:
                return []
            raster_ds = self.utci_raster
            value_name = 'UTCI'

        try:
            time_idx = None
            for i, t in enumerate(raster_ds.time.values):
                t_str = str(t)[:7]
                if t_str == date_input:
                    time_idx = i
                    break

            if time_idx is None:
                return []

            data_2d = raster_ds[value_name].isel(time=time_idx)

            polygon = None
            for feature in self.geojson['features']:
                if feature['properties'].get('name') == mo_name:
                    polygon = shape(feature['geometry'])
                    break

            if polygon is None:
                return []

            points = []
            lats = data_2d.latitude.values
            lons = data_2d.longitude.values

            for i, lat in enumerate(lats):
                for j, lon in enumerate(lons):
                    point = Point(lon, lat)
                    if polygon.contains(point):
                        val = data_2d.values[i, j]
                        if not np.isnan(val):
                            points.append({
                                'lat': float(lat),
                                'lon': float(lon),
                                'tci': float(val) if index_type == 'tci' else None,
                                'utci': float(val) if index_type == 'utci' else None
                            })

            return points

        except Exception as e:
            print(f"Ошибка получения точек растра: {e}")
            return []

    def get_raster_stats_by_district(self, mo_name, date_input, index_type='tci'):
        points = self.get_raster_points_by_district(mo_name, date_input, index_type)
        if not points:
            return None

        if index_type == 'tci':
            values = [p['tci'] for p in points if p['tci'] is not None]
        else:
            values = [p['utci'] for p in points if p['utci'] is not None]

        if not values:
            return None

        hist, bins = np.histogram(values, bins=10)

        return {
            'count': len(values),
            'min': float(min(values)),
            'max': float(max(values)),
            'mean': float(np.mean(values)),
            'std': float(np.std(values)),
            'histogram': [hist.tolist(), bins.tolist()]
        }

    def get_raster_points_by_period(self, mo_name, years_back, index_type='tci'):
        current_year = 2024
        start_year = current_year - years_back + 1

        all_points = []
        for year in range(start_year, current_year + 1):
            for month in range(1, 13):
                date_str = f"{year}-{month:02d}"
                points = self.get_raster_points_by_district(mo_name, date_str, index_type)
                all_points.extend(points)

        points_dict = {}
        for p in all_points:
            key = (p['lat'], p['lon'])
            if index_type == 'tci':
                val = p['tci']
            else:
                val = p['utci']

            if val is not None:
                if key not in points_dict:
                    points_dict[key] = {'lat': p['lat'], 'lon': p['lon'], 'values': []}
                points_dict[key]['values'].append(val)

        result = []
        for key, data in points_dict.items():
            avg_val = sum(data['values']) / len(data['values'])
            point = {'lat': data['lat'], 'lon': data['lon']}
            if index_type == 'tci':
                point['tci'] = avg_val
                point['utci'] = None
            else:
                point['tci'] = None
                point['utci'] = avg_val
            result.append(point)

        return result

    def get_raster_stats_by_period(self, mo_name, years_back, index_type='tci'):
        points = self.get_raster_points_by_period(mo_name, years_back, index_type)
        if not points:
            return None

        if index_type == 'tci':
            values = [p['tci'] for p in points if p['tci'] is not None]
        else:
            values = [p['utci'] for p in points if p['utci'] is not None]

        if not values:
            return None

        hist, bins = np.histogram(values, bins=10)

        return {
            'count': len(values),
            'min': float(min(values)),
            'max': float(max(values)),
            'mean': float(np.mean(values)),
            'std': float(np.std(values)),
            'histogram': [hist.tolist(), bins.tolist()]
        }

    def get_all_sights_by_category(self, category=None):
        if self.tourism_analyzer is None:
            return []
        return self.tourism_analyzer.get_all_sights_by_category(category)

    def get_sights_by_district(self, mo_name, category=None):
        if self.tourism_analyzer is None:
            return []
        return self.tourism_analyzer.get_sights_by_district(mo_name, category)

    def get_quadrant_analysis(self, month='07'):
        if self.tourism_analyzer is None:
            return {}
        return self.tourism_analyzer.get_quadrant_analysis(month)

    def get_sights_categories(self):
        if self.tourism_analyzer is None:
            return ['Все']
        return self.tourism_analyzer.get_sights_categories()

    def get_data_by_period(self, years_back, month):
        current_year = 2024
        start_year = current_year - years_back + 1

        period_rows = self.df[
            (self.df['time'].str[:4].astype(int).between(start_year, current_year)) &
            (self.df['time'].str[5:7] == month)
        ]

        if period_rows.empty:
            return None

        avg_row = period_rows.mean(numeric_only=True)
        avg_row['time'] = f"period-{years_back}-{month}"
        return avg_row