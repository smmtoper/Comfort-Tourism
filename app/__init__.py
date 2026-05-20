from flask import Flask


def create_app():
    app = Flask(__name__)

    DATA_PATH = r'C:\Users\sibsl\PycharmProjects\DEPLOM\tourism-climate\data\mo_climate_indexes.csv'
    GEOJSON_PATH = r'C:\Users\sibsl\PycharmProjects\DEPLOM\MO_Irk_region_4326.geojson'
    TCI_RASTER_PATH = r'C:\Users\sibsl\PycharmProjects\DEPLOM\tourism-climate\data\tci_final.nc'
    UTCI_RASTER_PATH = r'C:\Users\sibsl\PycharmProjects\DEPLOM\tourism-climate\data\utci_clean_fixed.nc'
    SIGHTS_PATH = r'C:\Users\sibsl\PycharmProjects\DEPLOM\tourism-climate\data\Irk_obl_sights.csv'

    from .routes import bp, init_data
    init_data(DATA_PATH, GEOJSON_PATH, TCI_RASTER_PATH, UTCI_RASTER_PATH, SIGHTS_PATH)

    app.register_blueprint(bp)

    return app