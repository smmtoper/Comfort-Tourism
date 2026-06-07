import os
import pandas as pd
import json
from pywps import Process, LiteralInput, LiteralOutput, Format


class TciGraph(Process):
    def __init__(self):
        inputs = [
            LiteralInput('mo', 'Муниципальное образование',
                         data_type='string',
                         abstract='Название МО')
        ]
        outputs = [
            LiteralOutput('result', 'Результат',
                          data_type='string',
                          output_format=Format('application/json'))
        ]

        self.csv_path = r'C:\Users\sibsl\PycharmProjects\DEPLOM\tourism-climate\data\mo_tci_timeseries_adjusted.csv'

        super().__init__(
            self._handler,
            identifier='tci_graph',
            title='Динамика TCI по годам',
            abstract='Возвращает массив {date, tci} для выбранного МО',
            version='1.0',
            inputs=inputs,
            outputs=outputs
        )

    def _handler(self, request, response):
        mo = request.inputs['mo'][0].data

        df = pd.read_csv(self.csv_path)

        if mo not in df['mo_name'].values:
            raise Exception(f'МО "{mo}" не найдено')

        row = df[df['mo_name'] == mo]
        dates = [col for col in df.columns if col != 'mo_name']
        values = row[dates].values[0]

        result = json.dumps([
            {'date': date, 'tci': float(values[i])}
            for i, date in enumerate(dates)
        ])

        response.outputs['result'].data = result
        return response