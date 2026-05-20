import pandas as pd
import numpy as np
import re


class TourismAnalyzer:
    def __init__(self, climate_df, sights_df, mo_list):
        self.climate_df = climate_df
        self.sights_df = sights_df
        self.mo_list = mo_list
        self._prepare_data()

    def _prepare_data(self):
        if self.sights_df is not None:
            # Очищаем координаты
            def clean_coord(value):
                if value is None or pd.isna(value):
                    return None
                value_str = str(value).replace(',', '.').strip()
                match = re.search(r'([-]?\d+\.?\d*)', value_str)
                if match:
                    try:
                        return float(match.group(1))
                    except:
                        return None
                return None

            self.sights_df['lat_clean'] = self.sights_df['lat'].apply(clean_coord)
            self.sights_df['lon_clean'] = self.sights_df['lon'].apply(clean_coord)

            # Удаляем строки с некорректными координатами
            self.sights_df = self.sights_df.dropna(subset=['lat_clean', 'lon_clean'])

            # Фильтруем координаты по границам Иркутской области
            self.sights_df = self.sights_df[
                (self.sights_df['lat_clean'] >= 50) & (self.sights_df['lat_clean'] <= 65) &
                (self.sights_df['lon_clean'] >= 95) & (self.sights_df['lon_clean'] <= 120)
                ]

            print(f"✅ После очистки координат: {len(self.sights_df)} объектов")

            # === НОРМАЛИЗАЦИЯ КАТЕГОРИЙ ===
            def normalize_category(row):
                cat = row['type']
                agr = row['agr_type']

                if pd.isna(cat) or cat == '':
                    cat = ''

                cat_lower = str(cat).lower()
                agr_lower = str(agr).lower() if not pd.isna(agr) else ''

                if cat_lower == '' or cat_lower == 'не определен':
                    if 'событийный' in agr_lower:
                        return 'Событийный'
                    if 'религиозный' in agr_lower:
                        return 'Религиозный'
                    if 'культурно-познавательный' in agr_lower:
                        return 'Культурно-познавательный'
                    if 'сельский' in agr_lower:
                        return 'Сельский'
                    if 'деловой' in agr_lower:
                        return 'Деловой'
                    if 'промышленный' in agr_lower:
                        return 'Промышленный'
                    if 'активный' in agr_lower:
                        return 'Активный'
                    return 'Другое'

                # Активный туризм
                if any(x in cat_lower for x in [
                    'бассейн', 'фитнес', 'спортивный', 'тренажёрный', 'стадион',
                    'скалодром', 'батутный', 'веревочный', 'горнолыжный', 'горнолыжная',
                    'лыжная', 'дайвинг', 'картинг', 'пейнтбол', 'лазертаг',
                    'спорт', 'stadiums', 'sport', 'pools', 'winter_sports', 'skiing',
                    'аквапарк', 'ледовый дворец', 'каток', 'спортплощадка',
                    'охотничье-рыболовные', 'вейк-клуб', 'сапсёрфинг', 'виндсёрфинг'
                ]):
                    return 'Активный'

                # Развлекательный туризм
                if any(x in cat_lower for x in [
                    'кинотеатр', 'развлекательный', 'парк аттракционов', 'квест',
                    'игровая', 'боулинг', 'клуб виртуальной', 'аттракцион',
                    'кафе', 'ресторан', 'торговый центр', 'цирк', 'cinemas', 'theatres',
                    'фотостудия', 'installation', 'sculptures', 'fountains', 'wall_painting',
                    'смотровая площадка', 'squares'
                ]):
                    return 'Развлекательный'

                # Лечебно-оздоровительный туризм
                if any(x in cat_lower for x in [
                    'санаторий', 'оздоровительный', 'лечебн', 'спа-салон',
                    'профилакторий', 'массажный', 'косметология', 'соляная пещера',
                    'санаторно-курортное объединение'
                ]):
                    return 'Лечебно-оздоровительный'

                # Культурно-познавательный туризм
                if any(x in cat_lower for x in [
                    'музей', 'выставочный', 'галерея', 'театр', 'филармония',
                    'концертный', 'планетарий', 'обсерватория', 'библиотека',
                    'памятник', 'мемориал', 'скульптура', 'исторический',
                    'архитектурный', 'усадьба', 'археологи', 'museums', 'art_galleries',
                    'monuments', 'memorials', 'theatre', 'культурный', 'историко',
                    'archaeology', 'cave_paintings'
                ]):
                    return 'Культурно-познавательный'

                # Природный туризм
                if any(x in cat_lower for x in [
                    'зоопарк', 'природный', 'водопад', 'гора', 'озеро', 'река',
                    'пещера', 'скала', 'лес', 'парк', 'сад', 'сквер', 'ботанический',
                    'заповедник', 'заказник', 'источник', 'родник', 'бухта', 'мыс',
                    'остров', 'natural', 'mountain', 'water', 'caves', 'gardens',
                    'waterfalls', 'geological', 'lake', 'river', 'park', 'природа',
                    'дендропарк', 'зооцентр'
                ]):
                    return 'Природный'

                # Религиозный туризм
                if any(x in cat_lower for x in [
                    'церковь', 'храм', 'монастырь', 'дацан', 'мечеть', 'синагога',
                    'собор', 'часовня', 'костел', 'религиозный', 'святыня',
                    'religion', 'churches', 'monasteries', 'cathedral', 'temple'
                ]):
                    return 'Религиозный'

                # Событийный туризм
                if any(x in cat_lower for x in [
                    'фестиваль', 'событийный', 'праздник', 'конкурс', 'ярмарка'
                ]):
                    return 'Событийный'

                # Сельский туризм
                if any(x in cat_lower for x in [
                    'сельский', 'ферма', 'усадьба', 'агротуризм', 'деревня'
                ]):
                    return 'Сельский'

                # Промышленный туризм
                if any(x in cat_lower for x in [
                    'промышленный', 'завод', 'фабрика', 'производство'
                ]):
                    return 'Промышленный'

                # Деловой туризм
                if any(x in cat_lower for x in [
                    'деловой', 'бизнес', 'конференц', 'выставка'
                ]):
                    return 'Деловой'

                return 'Другое'

            # Создаём колонку с нормализованными категориями
            self.sights_df['category_clean'] = self.sights_df.apply(normalize_category, axis=1)

            # === ОПРЕДЕЛЕНИЕ СЕЗОННОСТИ ОБЪЕКТОВ ===
            winter_keywords = [
                'горнолыж', 'лыжн', 'каток', 'ледов', 'коньк', 'сноуборд',
                'тюбинг', 'санк', 'зимн', 'снежн', 'лёд', 'лед', 'хоккей',
                'ski', 'snow', 'ice', 'winter', 'мороз', 'заснежен', 'сугроб',
                'биатлон', 'санный', 'бобслей', 'кёрлинг', 'фигурное катание',
                'горнолыжная база', 'горнолыжный курорт', 'ледовый дворец'
            ]

            summer_keywords = [
                'бассейн', 'пляж', 'плав', 'вейк', 'сап', 'каяк', 'рафт',
                'велос', 'трек', 'теннис', 'футбол', 'скейт', 'роллер',
                'водн', 'аквапарк', 'пляжный', 'купальн', 'велосипед', 'байк',
                'сплав', 'каноэ', 'яхта', 'катер', 'лодка', 'пеший поход',
                'треккинг', 'поход', 'туристическая тропа', 'экотропа',
                'пляжный волейбол', 'скейтборд', 'легкая атлетика', 'открытый бассейн'
            ]

            def get_season(row):
                name = str(row['name']).lower() if pd.notna(row['name']) else ''
                obj_type = str(row['type']).lower() if pd.notna(row['type']) else ''
                full_text = name + ' ' + obj_type

                if any(kw in full_text for kw in winter_keywords):
                    return 'winter'
                if any(kw in full_text for kw in summer_keywords):
                    return 'summer'
                return 'year'

            self.sights_df['season'] = self.sights_df.apply(get_season, axis=1)

            # Подсчёт достопримечательностей по районам и сезонам
            region_col = 'region (test_copies_deleted_6.csv1)'
            self.sights_count = self.sights_df[region_col].value_counts().to_dict()

            # Подсчёт по сезонам
            self.sights_count_winter = {}
            self.sights_count_summer = {}
            self.sights_count_year = {}

            for mo in self.mo_list:
                self.sights_count_winter[mo] = len(self.sights_df[
                                                       (self.sights_df[region_col] == mo) &
                                                       (self.sights_df['season'] == 'winter')
                                                       ])
                self.sights_count_summer[mo] = len(self.sights_df[
                                                       (self.sights_df[region_col] == mo) &
                                                       (self.sights_df['season'] == 'summer')
                                                       ])
                self.sights_count_year[mo] = len(self.sights_df[
                                                     (self.sights_df[region_col] == mo) &
                                                     (self.sights_df['season'] == 'year')
                                                     ])

            print(f"✅ Подсчёт сезонных объектов завершён")
            print(f"   Зимних объектов всего: {sum(self.sights_count_winter.values())}")
            print(f"   Летних объектов всего: {sum(self.sights_count_summer.values())}")
            print(f"   Круглогодичных: {sum(self.sights_count_year.values())}")

            # Список уникальных категорий для фильтра
            self.categories = ['Все'] + sorted(self.sights_df['category_clean'].unique())
            print(f"✅ Категории для фильтра: {self.categories}")

            # Статистика по категориям
            print("\n=== РАСПРЕДЕЛЕНИЕ ПО КАТЕГОРИЯМ ===")
            for cat in self.categories:
                if cat != 'Все':
                    count = len(self.sights_df[self.sights_df['category_clean'] == cat])
                    print(f"  {cat}: {count} объектов")
        else:
            self.sights_count = {}
            self.sights_count_winter = {}
            self.sights_count_summer = {}
            self.sights_count_year = {}
            self.categories = ['Все']

    def get_sights_count_by_season(self, mo_name, season_type):
        """Возвращает количество объектов в районе по сезону"""
        if season_type == 'winter':
            return self.sights_count_winter.get(mo_name, 0)
        elif season_type == 'summer':
            return self.sights_count_summer.get(mo_name, 0)
        else:
            return self.sights_count_year.get(mo_name, 0)

    def get_quadrant_analysis(self, month='07'):
        tci_row = self.climate_df[self.climate_df['time'].str.contains(f'-{month}')]
        if tci_row.empty:
            return {}
        tci_row = tci_row.iloc[0]

        tci_values = []
        sight_values = []
        valid_mos = []

        for mo in self.mo_list:
            tci_col = f'{mo}_tci'
            if tci_col in self.climate_df.columns:
                tci_val = tci_row[tci_col]
                if pd.notna(tci_val):
                    tci_values.append(float(tci_val))
                    sight_values.append(self.sights_count.get(mo, 0))
                    valid_mos.append(mo)

        if not tci_values:
            return {}

        tci_median = np.median(tci_values)
        sight_median = np.median(sight_values)

        quadrants = {}
        for i, mo in enumerate(valid_mos):
            tci = tci_values[i]
            count = sight_values[i]

            if tci >= tci_median and count >= sight_median:
                quadrant = "Эталонная территория"
                color = "#2ecc71"
                icon = "🏆"
            elif tci >= tci_median and count < sight_median:
                quadrant = "Спящий гигант"
                color = "#f39c12"
                icon = "😴"
            elif tci < tci_median and count >= sight_median:
                quadrant = "Устойчивый туризм"
                color = "#3498db"
                icon = "🏭"
            else:
                quadrant = "Сложная территория"
                color = "#e74c3c"
                icon = "⚠️"

            quadrants[mo] = {
                "quadrant": quadrant,
                "color": color,
                "icon": icon,
                "tci": round(tci, 1),
                "sights_count": count
            }

        return quadrants

    def get_sights_by_district(self, mo_name, category=None):
        if self.sights_df is None or self.sights_df.empty:
            return []

        region_col = 'region (test_copies_deleted_6.csv1)'
        result = self.sights_df[self.sights_df[region_col] == mo_name]

        if category and category != 'Все':
            result = result[result['category_clean'] == category]

        sights = []
        for _, row in result.iterrows():
            try:
                sights.append({
                    'name': str(row['name'])[:80],
                    'lat': float(row['lat_clean']),
                    'lon': float(row['lon_clean']),
                    'category': row['category_clean'],
                    'season': row['season'],
                    'address': str(row['address'])[:100] if pd.notna(row['address']) else ''
                })
            except:
                continue

        return sights

    def get_all_sights_by_category(self, category=None):
        if self.sights_df is None or self.sights_df.empty:
            return []

        result = self.sights_df

        if category and category != 'Все':
            result = result[result['category_clean'] == category]

        sights = []
        for _, row in result.iterrows():
            try:
                sights.append({
                    'name': str(row['name'])[:80],
                    'lat': float(row['lat_clean']),
                    'lon': float(row['lon_clean']),
                    'category': row['category_clean'],
                    'season': row['season'],
                    'address': str(row['address'])[:100] if pd.notna(row['address']) else ''
                })
            except:
                continue

        print(f"Категория '{category}': найдено {len(sights)} объектов")
        return sights

    def get_sights_categories(self):
        return self.categories