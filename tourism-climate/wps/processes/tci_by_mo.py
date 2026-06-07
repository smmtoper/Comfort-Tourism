import os
import pandas as pd
import json
from pywps import Process, LiteralInput, LiteralOutput
from pywps.app.exceptions import ProcessError


class TciByMo(Process):
    def __init__(self):
        inputs = [
            LiteralInput('mo', 'Муниципальное образование',
                         data_type='string',
                         abstract='Название МО (например: Иркутский)'),
            LiteralInput('date', 'Дата',
                         data_type='string',
                         abstract='Дата в формате ГГГГ-ММ (например: 2004-01)')
        ]
        outputs = [
            LiteralOutput('result', 'Результат',
                          data_type='string')
        ]

        # ПУТЬ К CSV
        self.csv_path = r'C:\Users\sibsl\PycharmProjects\DEPLOM\tourism-climate\data\mo_tci_timeseries_adjusted.csv'

        super().__init__(
            self._handler,
            identifier='tci_by_mo',
            title='TCI по муниципальному образованию',
            abstract='Возвращает значение TCI для указанного МО и даты',
            version='1.0',
            inputs=inputs,
            outputs=outputs
        )

    def _handler(self, request, response):
        try:
            # Получаем параметры
            mo = request.inputs['mo'][0].data
            date_input = request.inputs['date'][0].data

            # Читаем CSV
            if not os.path.exists(self.csv_path):
                raise ProcessError(f'Файл не найден: {self.csv_path}')

            df = pd.read_csv(self.csv_path)

            # Проверяем наличие колонки 'time'
            if 'time' not in df.columns:
                raise ProcessError(f'Нет колонки time. Доступны: {df.columns.tolist()}')

            # Проверяем существование МО
            if mo not in df.columns:
                available_mo = [col for col in df.columns if col != 'time'][:10]
                raise ProcessError(f'МО "{mo}" не найдено. Доступны: {available_mo}')

            # Приводим даты в CSV к строковому формату
            df['time'] = df['time'].astype(str)

            # Пробуем разные форматы для поиска даты
            found_date = None

            # Вариант 1: точное совпадение
            if date_input in df['time'].values:
                found_date = date_input

            # Вариант 2: поиск по началу строки (ГГГГ-ММ)
            if found_date is None:
                matching_dates = df[df['time'].str.startswith(date_input)]['time'].tolist()
                if matching_dates:
                    found_date = matching_dates[0]

            # Вариант 3: для запросов с днем (если передали полную дату)
            if found_date is None and len(date_input) == 10:
                if date_input in df['time'].values:
                    found_date = date_input

            if found_date is None:
                available_dates = df['time'].tolist()[:5]
                raise ProcessError(f'Дата "{date_input}" не найдена. Доступны: {available_dates}')

            # Получаем значение TCI
            tci_value = df[df['time'] == found_date][mo].values[0]

            # Формируем JSON
            result = json.dumps({
                'mo': mo,
                'date': found_date,
                'tci': float(tci_value) if pd.notna(tci_value) else None
            }, ensure_ascii=False)

            response.outputs['result'].data = result
            response.content_type = 'application/json'

        except Exception as e:
            raise ProcessError(f'Ошибка: {str(e)}')

        return response