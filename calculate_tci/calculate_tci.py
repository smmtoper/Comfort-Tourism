"""
Расчёт TCI (Tourism Climate Index) по Mieczkowski (1985)
на ежемесячных данных ERA5.
"""

import xarray as xr
import numpy as np
import pandas as pd

# =============================================================================
# БИВАРИАТНАЯ ТАБЛИЦА ТЕПЛОВОГО КОМФОРТА (Mieczkowski, 1985, Figure 1)
# =============================================================================

# Пороговые значения температуры (°C) — нижние границы интервалов
T_BREAKS = [-np.inf, -30, -25, -20, -15, -10, -5, 0, 5, 10, 14, 18, 22, 26, 30, 34, np.inf]

# Пороговые значения RH (%) — нижние границы интервалов
RH_BREAKS = [0, 20, 40, 60, 80, 100]

# Матрица баллов: строки = T-интервалы, столбцы = RH-интервалы
# По Mieczkowski (1985), Figure 1 / Thermal Comfort diagram (адаптация ASHRAE 1972)
CI_TABLE = np.array([
    # RH: 0-20  20-40  40-60  60-80  80-100
    [-3, -3, -3, -3, -3],  # T < -30
    [-3, -3, -3, -3, -3],  # -30 ≤ T < -25
    [-2, -2, -3, -3, -3],  # -25 ≤ T < -20
    [-1, -1, -2, -2, -3],  # -20 ≤ T < -15
    [0, 0, -1, -1, -2],  # -15 ≤ T < -10
    [1, 1, 0, 0, -1],  # -10 ≤ T < -5
    [2, 2, 1, 1, 0],  # -5 ≤ T < 0
    [1, 2, 2, 1, 0],  # 0 ≤ T < 5
    [1, 2, 3, 2, 1],  # 5 ≤ T < 10
    [2, 3, 4, 3, 2],  # 10 ≤ T < 14
    [3, 4, 5, 4, 3],  # 14 ≤ T < 18
    [3, 4, 5, 4, 3],  # 18 ≤ T < 22
    [3, 4, 5, 4, 2],  # 22 ≤ T < 26
    [2, 3, 4, 3, 1],  # 26 ≤ T < 30
    [1, 2, 2, 1, -1],  # 30 ≤ T < 34
    [0, 1, 1, -1, -3],  # T ≥ 34
], dtype=float)


def ci_lookup(t: xr.DataArray, rh: xr.DataArray) -> xr.DataArray:
    """
    Возвращает балл теплового комфорта по бивариатной таблице Mieczkowski.

    Parameters
    ----------
    t  : xr.DataArray — температура воздуха (°C)
    rh : xr.DataArray — относительная влажность (%)

    Returns
    -------
    xr.DataArray — балл CI от -3 до +5
    """
    # Индексируем строку по температуре
    t_idx = np.digitize(t.values, bins=T_BREAKS[1:])
    t_idx = np.clip(t_idx, 0, len(T_BREAKS) - 2)

    # Индексируем столбец по влажности
    rh_idx = np.digitize(rh.values, bins=RH_BREAKS[1:])
    rh_idx = np.clip(rh_idx, 0, len(RH_BREAKS) - 2)

    # Vectorized lookup
    score_values = CI_TABLE[t_idx, rh_idx]

    return xr.DataArray(score_values, coords=t.coords, dims=t.dims)


# =============================================================================
# ТАБЛИЦЫ СУБИНДЕКСОВ R, S, W (Mieczkowski, 1985, Table 1)
# =============================================================================

def r_score(tp: xr.DataArray) -> xr.DataArray:
    """Субиндекс осадков R. tp — месячная сумма осадков (мм)."""
    s = xr.full_like(tp, 0.0)
    s = xr.where(tp < 15, 5.0, s)
    s = xr.where((tp >= 15) & (tp < 30), 4.5, s)
    s = xr.where((tp >= 30) & (tp < 50), 4.0, s)
    s = xr.where((tp >= 50) & (tp < 60), 3.5, s)
    s = xr.where((tp >= 60) & (tp < 75), 3.0, s)
    s = xr.where((tp >= 75) & (tp < 90), 2.5, s)
    s = xr.where((tp >= 90) & (tp < 105), 2.0, s)
    s = xr.where((tp >= 105) & (tp < 120), 1.5, s)
    s = xr.where((tp >= 120) & (tp < 135), 1.0, s)
    s = xr.where((tp >= 135) & (tp < 150), 0.5, s)
    s = xr.where(tp >= 150, 0.0, s)
    return s


def s_score(sunshine_hrs: xr.DataArray) -> xr.DataArray:
    """Субиндекс инсоляции S. sunshine_hrs — среднесуточная инсоляция (часы)."""
    s = xr.full_like(sunshine_hrs, 0.0)
    s = xr.where(sunshine_hrs >= 10, 5.0, s)
    s = xr.where((sunshine_hrs >= 9) & (sunshine_hrs < 10), 4.5, s)
    s = xr.where((sunshine_hrs >= 8) & (sunshine_hrs < 9), 4.0, s)
    s = xr.where((sunshine_hrs >= 7) & (sunshine_hrs < 8), 3.5, s)
    s = xr.where((sunshine_hrs >= 6) & (sunshine_hrs < 7), 3.0, s)
    s = xr.where((sunshine_hrs >= 5) & (sunshine_hrs < 6), 2.5, s)
    s = xr.where((sunshine_hrs >= 4) & (sunshine_hrs < 5), 2.0, s)
    s = xr.where((sunshine_hrs >= 3) & (sunshine_hrs < 4), 1.5, s)
    s = xr.where((sunshine_hrs >= 2) & (sunshine_hrs < 3), 1.0, s)
    s = xr.where((sunshine_hrs >= 1) & (sunshine_hrs < 2), 0.5, s)
    s = xr.where(sunshine_hrs < 1, 0.0, s)
    return s


def w_score(ws: xr.DataArray) -> xr.DataArray:
    """Субиндекс ветра W. ws — среднемесячная скорость ветра (м/с)."""
    s = xr.full_like(ws, 0.0)
    s = xr.where(ws < 0.8, 5.0, s)
    s = xr.where((ws >= 0.8) & (ws < 1.6), 4.5, s)
    s = xr.where((ws >= 1.6) & (ws < 2.6), 4.0, s)
    s = xr.where((ws >= 2.6) & (ws < 3.4), 3.5, s)
    s = xr.where((ws >= 3.4) & (ws < 5.5), 3.0, s)
    s = xr.where((ws >= 5.5) & (ws < 6.8), 2.5, s)
    s = xr.where((ws >= 6.8) & (ws < 8.0), 2.0, s)
    s = xr.where((ws >= 8.0) & (ws < 10.8), 1.0, s)
    s = xr.where(ws >= 10.8, 0.0, s)
    return s


# =============================================================================
# ОСНОВНОЙ РАСЧЁТ
# =============================================================================

def calc_tci(ds: xr.Dataset) -> xr.Dataset:
    """
    Рассчитывает TCI по Mieczkowski (1985) на подготовленном датасете.

    Ожидаемые переменные в ds:
        T_max   — средняя месячная максимальная температура воздуха (°C)
        RH_min  — средняя месячная минимальная относительная влажность (%)
        t_mean  — среднемесячная температура воздуха (°C)
        RH_mean — среднемесячная относительная влажность (%)
        tp      — месячная сумма осадков (мм)
        S       — среднесуточная продолжительность солнечного сияния (часы)
        ws      — среднемесячная скорость ветра (м/с)

    Возвращает ds с добавленными переменными:
        CId, CIa, R_score, S_score, W_score, TCI
    """
    print("Расчёт субиндексов TCI по Mieczkowski (1985)...")

    # CId: дневной комфорт (макс. T + мин. RH)
    print("  CId: максимальная T + минимальная RH → таблица Mieczkowski...")
    ds['CId'] = ci_lookup(ds['T_max'], ds['RH_min'])

    # CIa: суточный комфорт (средняя T + средняя RH)
    print("  CIa: средняя T + средняя RH → таблица Mieczkowski...")
    ds['CIa'] = ci_lookup(ds['t_mean'], ds['RH_mean'])

    # R: осадки
    print("  R: осадки...")
    ds['R_score'] = r_score(ds['tp'])

    # S: инсоляция
    print("  S: инсоляция (часы/сутки)...")
    ds['S_score'] = s_score(ds['S'])

    # W: ветер
    print("  W: скорость ветра...")
    ds['W_score'] = w_score(ds['ws'])

    # Итоговый TCI
    print("\nРасчёт итогового TCI...")
    ds['TCI'] = (
            8 * ds['CId'] +
            4 * ds['CIa'] +
            4 * ds['R_score'] +
            2 * ds['S_score'] +
            2 * ds['W_score']
    )

    return ds


def print_stats(ds: xr.Dataset):
    """Печатает статистику по субиндексам и TCI."""
    print("\n" + "=" * 55)
    print("СТАТИСТИКА")
    print("=" * 55)
    for var in ['CId', 'CIa', 'R_score', 'S_score', 'W_score', 'TCI']:
        if var in ds.data_vars:
            mn = float(ds[var].min())
            mx = float(ds[var].max())
            avg = float(ds[var].mean())
            print(f"  {var:<10} мин={mn:6.2f}  макс={mx:6.2f}  среднее={avg:6.2f}")

    if 'TCI' in ds.data_vars:
        print("\nРаспределение TCI по категориям Mieczkowski (1985):")
        tci = ds['TCI'].values.flatten()
        tci = tci[~np.isnan(tci)]
        categories = [
            ("Идеально", 90, 100),
            ("Отлично", 80, 90),
            ("Очень хорошо", 70, 80),
            ("Хорошо", 60, 70),
            ("Приемлемо", 50, 60),
            ("Возможно", 40, 50),
            ("Нежелательно", 30, 40),
            ("Очень нежелательно", 20, 30),
            ("Крайне нежелательно", 10, 20),
            ("Невозможно", -40, 10),
        ]
        total = len(tci)
        for label, lo, hi in categories:
            n = np.sum((tci >= lo) & (tci < hi))
            pct = 100 * n / total if total > 0 else 0
            print(f"  {label:<26} ({lo:>4}–{hi:>3}): {n:>6} ячеек ({pct:.1f}%)")