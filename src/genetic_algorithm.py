"""
Genetic Algorithm for Feature Selection
Evolves optimal subset of URL features to maximize classification F1-score.

Custom implementation from scratch - no external GA library used.
"""

import numpy as np
import random
import json
import os
import time
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score


# ========================================
# GENETIC ALGORITHM CONFIGURATION
# ========================================

GA_CONFIG = {
    'population_size': 40,       # Number of chromosomes per generation
    'num_generations': 30,       # Maximum generations
    'crossover_rate': 0.8,       # Probability of crossover
    'mutation_rate': 0.03,       # Probability of bit flip per gene
    'tournament_size': 5,        # Tournament selection pool size
    'elitism_count': 2,          # Top N chromosomes preserved unchanged
    'min_features': 5,           # Minimum features in a chromosome
    'early_stop_patience': 10,   # Stop if no improvement for N generations
    'cv_folds': 5,               # Cross-validation folds
    'random_seed': 42,
}


# ========================================
# CHROMOSOME REPRESENTATION
# ========================================
# Each chromosome is a binary array of length = num_features
# 1 = feature is selected, 0 = feature is excluded
# Example: [1, 0, 1, 1, 0, ...] means features 0, 2, 3 are used


class GeneticAlgorithm:
    """
    Genetic Algorithm for feature selection.

    Uses binary chromosome encoding where each gene represents
    whether a feature is included (1) or excluded (0).
    """

    def __init__(self, X, y, feature_names, config=None):
        """
        Initialize the GA.

        Parameters:
            X (np.ndarray): Feature matrix (n_samples, n_features)
            y (np.ndarray): Labels (n_samples,)
            feature_names (list): Names of features
            config (dict): GA configuration overrides
        """
        self.X = np.array(X)
        self.y = np.array(y)
        self.feature_names = feature_names
        self.num_features = len(feature_names)

        # Merge config with defaults
        self.config = {**GA_CONFIG, **(config or {})}

        # Set random seed for reproducibility
        random.seed(self.config['random_seed'])
        np.random.seed(self.config['random_seed'])

        # Tracking
        self.history = {
            'best_fitness': [],
            'avg_fitness': [],
            'num_features_selected': [],
            'best_chromosome': [],
        }
        self.best_chromosome = None
        self.best_fitness = 0.0

    # ========================================
    # POPULATION INITIALIZATION
    # ========================================

    def initialize_population(self):
        """
        Create initial population of random chromosomes.
        Each chromosome has at least min_features genes set to 1.
        """
        population = []
        for _ in range(self.config['population_size']):
            # Random binary chromosome
            chromosome = np.random.randint(0, 2, size=self.num_features)

            # Ensure minimum features are selected
            while np.sum(chromosome) < self.config['min_features']:
                idx = random.randint(0, self.num_features - 1)
                chromosome[idx] = 1

            population.append(chromosome)

        # Always include an "all features" chromosome
        population[0] = np.ones(self.num_features, dtype=int)

        return population

    # ========================================
    # FITNESS FUNCTION
    # ========================================

    def calculate_fitness(self, chromosome):
        """
        Evaluate chromosome fitness using cross-validated F1-score.

        Parameters:
            chromosome (np.ndarray): Binary feature mask

        Returns:
            float: Mean F1-score from cross-validation
        """
        # Get selected feature indices
        selected = np.where(chromosome == 1)[0]

        if len(selected) < self.config['min_features']:
            return 0.0  # Penalty for too few features

        # Subset features
        X_subset = self.X[:, selected]

        # Train and evaluate with cross-validation
        clf = RandomForestClassifier(
            n_estimators=50,  # Reduced for speed during GA
            max_depth=10,
            class_weight='balanced',
            random_state=self.config['random_seed'],
            n_jobs=-1
        )

        try:
            scores = cross_val_score(
                clf, X_subset, self.y,
                cv=self.config['cv_folds'],
                scoring='f1',
                n_jobs=-1
            )
            fitness = scores.mean()
        except Exception:
            fitness = 0.0

        return round(fitness, 6)

    # ========================================
    # SELECTION: Tournament Selection
    # ========================================

    def tournament_selection(self, population, fitness_scores):
        """
        Select a parent using tournament selection.
        Randomly picks `tournament_size` individuals and returns the best.
        """
        tournament_size = self.config['tournament_size']
        tournament_indices = random.sample(range(len(population)), tournament_size)
        tournament_fitness = [(i, fitness_scores[i]) for i in tournament_indices]
        winner_idx = max(tournament_fitness, key=lambda x: x[1])[0]
        return population[winner_idx].copy()

    # ========================================
    # CROSSOVER: Single-Point Crossover
    # ========================================

    def crossover(self, parent1, parent2):
        """
        Perform single-point crossover between two parents.
        A random crossover point is chosen; genes are swapped after that point.
        """
        if random.random() > self.config['crossover_rate']:
            return parent1.copy(), parent2.copy()

        # Choose crossover point
        point = random.randint(1, self.num_features - 1)

        # Create children by swapping
        child1 = np.concatenate([parent1[:point], parent2[point:]])
        child2 = np.concatenate([parent2[:point], parent1[point:]])

        return child1, child2

    # ========================================
    # MUTATION: Bit-Flip Mutation
    # ========================================

    def mutate(self, chromosome):
        """
        Apply bit-flip mutation.
        Each gene has a `mutation_rate` probability of being flipped.
        """
        mutated = chromosome.copy()
        for i in range(self.num_features):
            if random.random() < self.config['mutation_rate']:
                mutated[i] = 1 - mutated[i]  # Flip bit

        # Ensure minimum features
        while np.sum(mutated) < self.config['min_features']:
            idx = random.randint(0, self.num_features - 1)
            mutated[idx] = 1

        return mutated

    # ========================================
    # ELITISM
    # ========================================

    def apply_elitism(self, population, fitness_scores, new_population):
        """
        Preserve top N chromosomes from current generation unchanged.
        """
        elite_count = self.config['elitism_count']
        elite_indices = np.argsort(fitness_scores)[-elite_count:]

        for i, idx in enumerate(elite_indices):
            new_population[i] = population[idx].copy()

        return new_population

    # ========================================
    # MAIN EVOLUTION LOOP
    # ========================================

    def evolve(self):
        """
        Run the full Genetic Algorithm.

        Returns:
            dict: Results containing best chromosome, selected features, fitness history
        """
        print("\n" + "=" * 70)
        print("  GENETIC ALGORITHM -- Feature Selection")
        print("=" * 70)
        print(f"  Population size:    {self.config['population_size']}")
        print(f"  Max generations:    {self.config['num_generations']}")
        print(f"  Crossover rate:     {self.config['crossover_rate']}")
        print(f"  Mutation rate:      {self.config['mutation_rate']}")
        print(f"  Tournament size:    {self.config['tournament_size']}")
        print(f"  Elitism count:      {self.config['elitism_count']}")
        print(f"  Total features:     {self.num_features}")
        print("=" * 70)

        # Initialize population
        population = self.initialize_population()
        no_improve_count = 0
        start_time = time.time()

        for gen in range(self.config['num_generations']):
            gen_start = time.time()

            # ---- Evaluate fitness for all chromosomes ----
            fitness_scores = []
            for chromosome in population:
                fitness = self.calculate_fitness(chromosome)
                fitness_scores.append(fitness)

            # ---- Track statistics ----
            best_idx = np.argmax(fitness_scores)
            gen_best_fitness = fitness_scores[best_idx]
            gen_avg_fitness = np.mean(fitness_scores)
            gen_best_features = int(np.sum(population[best_idx]))

            self.history['best_fitness'].append(gen_best_fitness)
            self.history['avg_fitness'].append(gen_avg_fitness)
            self.history['num_features_selected'].append(gen_best_features)
            self.history['best_chromosome'].append(population[best_idx].tolist())

            # Update global best
            if gen_best_fitness > self.best_fitness:
                self.best_fitness = gen_best_fitness
                self.best_chromosome = population[best_idx].copy()
                no_improve_count = 0
            else:
                no_improve_count += 1

            gen_time = time.time() - gen_start

            # ---- Print progress ----
            print(f"  Gen {gen+1:3d}/{self.config['num_generations']}  |  "
                  f"Best F1: {gen_best_fitness:.4f}  |  "
                  f"Avg F1: {gen_avg_fitness:.4f}  |  "
                  f"Features: {gen_best_features}/{self.num_features}  |  "
                  f"Time: {gen_time:.1f}s")

            # ---- Early stopping ----
            if no_improve_count >= self.config['early_stop_patience']:
                print(f"\n  [!] Early stopping: No improvement for {self.config['early_stop_patience']} generations")
                break

            # ---- Create next generation ----
            new_population = [np.zeros(self.num_features, dtype=int) for _ in range(self.config['population_size'])]

            # Elitism -- keep best chromosomes
            new_population = self.apply_elitism(population, fitness_scores, new_population)

            # Fill rest with crossover + mutation
            start_idx = self.config['elitism_count']
            while start_idx < self.config['population_size']:
                # Select parents
                parent1 = self.tournament_selection(population, fitness_scores)
                parent2 = self.tournament_selection(population, fitness_scores)

                # Crossover
                child1, child2 = self.crossover(parent1, parent2)

                # Mutation
                child1 = self.mutate(child1)
                child2 = self.mutate(child2)

                new_population[start_idx] = child1
                if start_idx + 1 < self.config['population_size']:
                    new_population[start_idx + 1] = child2
                start_idx += 2

            population = new_population

        # ========================================
        # RESULTS
        # ========================================
        total_time = time.time() - start_time
        selected_indices = np.where(self.best_chromosome == 1)[0]
        selected_names = [self.feature_names[i] for i in selected_indices]
        dropped_names = [self.feature_names[i] for i in range(self.num_features)
                        if self.best_chromosome[i] == 0]

        print("\n" + "=" * 70)
        print("  GA RESULTS")
        print("=" * 70)
        print(f"  Best F1-Score:      {self.best_fitness:.4f}")
        print(f"  Features selected:  {len(selected_names)}/{self.num_features}")
        print(f"  Total time:         {total_time:.1f}s")
        print(f"\n  Selected features:")
        for i, name in enumerate(selected_names):
            print(f"    {i+1:2d}. {name}")
        if dropped_names:
            print(f"\n  Dropped features:")
            for name in dropped_names:
                print(f"    -  {name}")
        print("=" * 70)

        results = {
            'best_fitness': self.best_fitness,
            'best_chromosome': self.best_chromosome.tolist(),
            'selected_features': selected_names,
            'selected_indices': selected_indices.tolist(),
            'dropped_features': dropped_names,
            'num_selected': len(selected_names),
            'num_total': self.num_features,
            'history': {
                'best_fitness': self.history['best_fitness'],
                'avg_fitness': self.history['avg_fitness'],
                'num_features_selected': self.history['num_features_selected'],
            },
            'config': self.config,
            'total_time_seconds': round(total_time, 2),
        }

        return results


def save_ga_results(results, output_dir):
    """Save GA results to JSON file."""
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, "selected_features.json")
    with open(filepath, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"  [+] GA results saved to: {filepath}")
    return filepath


# ========================================
# STANDALONE TEST
# ========================================
if __name__ == "__main__":
    from sklearn.datasets import make_classification

    print("Testing GA with synthetic data...")

    # Create dummy data with 33 features (some informative, some noise)
    X, y = make_classification(
        n_samples=500, n_features=33, n_informative=15,
        n_redundant=5, n_classes=2, random_state=42
    )

    feature_names = [f"feature_{i}" for i in range(33)]

    ga = GeneticAlgorithm(X, y, feature_names, config={
        'population_size': 20,
        'num_generations': 10,
    })

    results = ga.evolve()
    print(f"\nTest complete. Selected {results['num_selected']}/{results['num_total']} features.")
