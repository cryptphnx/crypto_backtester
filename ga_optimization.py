# ga_optimization.py
import random
import multiprocessing
from deap import base, creator, tools, algorithms
import backtrader as bt
from data import get_historical_data
from strategy import PineStrategy
from backtesting import run_backtest

# Update parameter boundaries for 20 parameters.
PARAM_BOUNDARIES = [
    (10, 200),      # longTermFastLen
    (100, 400),     # longTermSlowLen
    (5, 20),        # shortTermFastLen
    (15, 30),       # shortTermSlowLen
    (1, 10),        # fixedStopLossPct: from 1 to 10
    (1, 10),        # fixedTakeProfitPct: from 1 to 10
    (1, 10),        # fixedTrailingPct: from 1 to 10
    (0, 1),         # useAdxFilter
    (10, 18),       # adxPeriod
    (15.0, 25.0),   # adxThreshold
    (0, 1),         # useVolumeFilter
    (15, 25),       # volumeMALen
    (0, 1),         # useRSIFilter
    (10, 18),       # rsiPeriod
    (45.0, 55.0),   # rsiLongThreshold
    (45.0, 55.0),   # rsiShortThreshold
    (0, 1),         # useAtrFilter
    (0.005, 0.015), # atrFilterThreshold
    (0, 1),         # enableHigherTFFilter
    (0, 1)          # enableSessionFilter
]
NUM_PARAMS = len(PARAM_BOUNDARIES)  # 20 parameters

creator.create("FitnessMax", base.Fitness, weights=(1.0,))
creator.create("Individual", list, fitness=creator.FitnessMax)

toolbox = base.Toolbox()

def random_gene(bound):
    return random.uniform(bound[0], bound[1])

def create_individual():
    return [random_gene(bound) for bound in PARAM_BOUNDARIES]

toolbox.register("individual", tools.initIterate, creator.Individual, create_individual)
toolbox.register("population", tools.initRepeat, list, toolbox.individual)

def eval_individual(individual):
    params = {
        "longTermFastLen": int(round(individual[0])),
        "longTermSlowLen": int(round(individual[1])),
        "shortTermFastLen": int(round(individual[2])),
        "shortTermSlowLen": int(round(individual[3])),
        "fixedStopLossPct": float(individual[4]),
        "fixedTakeProfitPct": float(individual[5]),
        "fixedTrailingPct": float(individual[6]),
        "useAdxFilter": True if individual[7] >= 0.5 else False,
        "adxPeriod": int(round(individual[8])),
        "adxThreshold": float(individual[9]),
        "useVolumeFilter": True if individual[10] >= 0.5 else False,
        "volumeMALen": int(round(individual[11])),
        "useRSIFilter": True if individual[12] >= 0.5 else False,
        "rsiPeriod": int(round(individual[13])),
        "rsiLongThreshold": float(individual[14]),
        "rsiShortThreshold": float(individual[15]),
        "useAtrFilter": True if individual[16] >= 0.5 else False,
        "atrFilterThreshold": float(individual[17]),
        "enableHigherTFFilter": True if individual[18] >= 0.5 else False,
        "enableSessionFilter": True if individual[19] >= 0.5 else False,
    }
    try:
        init_val, final_val, trade_log, cerebro = run_backtest(
            symbol='BTCUSDT',
            timeframe='5m',
            start_str='1 month ago UTC',
            strategy_params=params
        )
    except Exception as e:
        print("Error during backtest:", e)
        return (-1e6,)
    
    return (final_val,)

toolbox.register("evaluate", eval_individual)
toolbox.register("mate", tools.cxBlend, alpha=0.5)
toolbox.register("mutate", tools.mutGaussian, mu=0, sigma=1.0, indpb=0.2)
toolbox.register("select", tools.selTournament, tournsize=3)

def run_optimization(symbol='BTCUSDT', timeframe='5m', start_str='1 month ago UTC'):
    random.seed(42)
    
    pool = multiprocessing.Pool(processes=multiprocessing.cpu_count())
    toolbox.register("map", pool.map)
    
    pop = toolbox.population(n=50)
    ngen = 10
    cxpb = 0.5
    mutpb = 0.2

    print("Starting GA optimization with population size:", len(pop), "and generations:", ngen)
    pop, logbook = algorithms.eaSimple(pop, toolbox, cxpb, mutpb, ngen, verbose=True)
    
    best_ind = tools.selBest(pop, 1)[0]
    best_value = best_ind.fitness.values[0]
    
    best_params = {
        "longTermFastLen": int(round(best_ind[0])),
        "longTermSlowLen": int(round(best_ind[1])),
        "shortTermFastLen": int(round(best_ind[2])),
        "shortTermSlowLen": int(round(best_ind[3])),
        "fixedStopLossPct": float(best_ind[4]),
        "fixedTakeProfitPct": float(best_ind[5]),
        "fixedTrailingPct": float(best_ind[6]),
        "useAdxFilter": True if best_ind[7] >= 0.5 else False,
        "adxPeriod": int(round(best_ind[8])),
        "adxThreshold": float(best_ind[9]),
        "useVolumeFilter": True if best_ind[10] >= 0.5 else False,
        "volumeMALen": int(round(best_ind[11])),
        "useRSIFilter": True if best_ind[12] >= 0.5 else False,
        "rsiPeriod": int(round(best_ind[13])),
        "rsiLongThreshold": float(best_ind[14]),
        "rsiShortThreshold": float(best_ind[15]),
        "useAtrFilter": True if best_ind[16] >= 0.5 else False,
        "atrFilterThreshold": float(best_ind[17]),
        "enableHigherTFFilter": True if best_ind[18] >= 0.5 else False,
        "enableSessionFilter": True if best_ind[19] >= 0.5 else False,
    }
    
    print("Best Final Portfolio Value:", best_value)
    print("Best Parameters:", best_params)
    
    pool.close()
    pool.join()
    
    return best_value, best_params

if __name__ == "__main__":
    best_value, best_params = run_optimization()
    print(f"Best Portfolio Value: {best_value}")
    print("Best Parameters:", best_params)
