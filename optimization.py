import random
from deap import base, creator, tools, algorithms
from backtesting import run_backtest

# Define parameter boundaries for 20 parameters in order:
# Order:
#  0: longTermFastLen (int, [10, 200])
#  1: longTermSlowLen (int, [100, 400])
#  2: shortTermFastLen (int, [5, 20])
#  3: shortTermSlowLen (int, [15, 30])
#  4: fixedStopLossPct (float, [0.005, 0.11])
#  5: fixedTakeProfitPct (float, [0.015, 0.12])
#  6: fixedTrailingPct (float, [0.005, 0.11])
#  7: useAdxFilter (bool as float, [0, 1])
#  8: adxPeriod (int, [10, 18])
#  9: adxThreshold (float, [15.0, 25.0])
# 10: useVolumeFilter (bool, [0, 1])
# 11: volumeMALen (int, [15, 25])
# 12: useRSIFilter (bool, [0, 1])
# 13: rsiPeriod (int, [10, 18])
# 14: rsiLongThreshold (float, [45.0, 55.0])
# 15: rsiShortThreshold (float, [45.0, 55.0])
# 16: useAtrFilter (bool, [0, 1])
# 17: atrFilterThreshold (float, [0.005, 0.015])
# 18: enableHigherTFFilter (bool, [0, 1])
# 19: enableSessionFilter (bool, [0, 1])
PARAM_BOUNDARIES = [
    (10, 200),      # longTermFastLen
    (100, 400),     # longTermSlowLen
    (5, 20),        # shortTermFastLen
    (15, 30),       # shortTermSlowLen
    (0.005, 0.11),  # fixedStopLossPct
    (0.015, 0.12),  # fixedTakeProfitPct
    (0.005, 0.11),  # fixedTrailingPct
    (0, 1),         # useAdxFilter (0=False, 1=True)
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
NUM_PARAMS = len(PARAM_BOUNDARIES)  # Should be 20

# Set up the DEAP framework
creator.create("FitnessMax", base.Fitness, weights=(1.0,))
creator.create("Individual", list, fitness=creator.FitnessMax)

toolbox = base.Toolbox()

# Attribute generator: generate a random value for a gene given its boundaries.
def random_gene(bound):
    return random.uniform(bound[0], bound[1])

def create_individual():
    return [random_gene(bound) for bound in PARAM_BOUNDARIES]

toolbox.register("individual", tools.initIterate, creator.Individual, create_individual)
toolbox.register("population", tools.initRepeat, list, toolbox.individual)

# Fitness evaluation function: run the backtest with the given parameters and return final portfolio value.
def eval_individual(individual):
    # Convert the individual list into a strategy parameters dictionary.
    params = {}
    # Strategy parameters (indices 0-6):
    params["longTermFastLen"] = int(round(individual[0]))
    params["longTermSlowLen"] = int(round(individual[1]))
    params["shortTermFastLen"] = int(round(individual[2]))
    params["shortTermSlowLen"] = int(round(individual[3]))
    params["fixedStopLossPct"] = float(individual[4])
    params["fixedTakeProfitPct"] = float(individual[5])
    params["fixedTrailingPct"] = float(individual[6])
    # Filter parameters (indices 7-19):
    params["useAdxFilter"] = True if individual[7] >= 0.5 else False
    params["adxPeriod"] = int(round(individual[8]))
    params["adxThreshold"] = float(individual[9])
    params["useVolumeFilter"] = True if individual[10] >= 0.5 else False
    params["volumeMALen"] = int(round(individual[11]))
    params["useRSIFilter"] = True if individual[12] >= 0.5 else False
    params["rsiPeriod"] = int(round(individual[13]))
    params["rsiLongThreshold"] = float(individual[14])
    params["rsiShortThreshold"] = float(individual[15])
    params["useAtrFilter"] = True if individual[16] >= 0.5 else False
    params["atrFilterThreshold"] = float(individual[17])
    params["enableHigherTFFilter"] = True if individual[18] >= 0.5 else False
    params["enableSessionFilter"] = True if individual[19] >= 0.5 else False

    try:
        # Run backtest with these parameters.
        # Here we use a fixed symbol/timeframe for demonstration.
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

def main():
    random.seed(42)
    pop = toolbox.population(n=50)  # Starting population of 50 individuals.
    ngen = 10  # Run for 10 generations (adjust as needed)
    cxpb = 0.5  # Crossover probability
    mutpb = 0.2  # Mutation probability

    print("Starting GA optimization with population size:", len(pop), "and generations:", ngen)
    pop, logbook = algorithms.eaSimple(pop, toolbox, cxpb, mutpb, ngen, verbose=True)
    
    best_ind = tools.selBest(pop, 1)[0]
    best_value = best_ind.fitness.values[0]
    
    # Convert best individual into a parameters dictionary.
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
    return best_params, best_value

if __name__ == "__main__":
    best_params, best_value = main()
