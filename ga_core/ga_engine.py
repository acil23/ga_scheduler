import copy
from ga_core.individual import Individual
from ga_core.fitness import FitnessCalculator
import ga_core.operators as ops
from ga_core.local_search import LocalSearch

class GeneticAlgorithm:
    def __init__(self, data, params):
        self.data = data
        self.params = params
        
        self.classes = data['classes']
        self.slots = data['slots']
        self.rooms = data['rooms']
        self.candidates = data['candidates']
        self.pref_info = data['pref_info']
        
        self.fitness_calc = FitnessCalculator(self.slots, self.rooms)
        
        # Inisialisasi Local Search
        self.ls_engine = LocalSearch(self.fitness_calc, self.candidates, self.pref_info)
        
        self.population = []
        self.best_individual = None
        self.history = []

    def initialize_population(self):
        print(">>> Inisialisasi Populasi Awal...")
        self.population = []
        for _ in range(self.params['pop_size']):
            ind = Individual(self.classes, self.slots, self.rooms)
            ind.initialize_random()
            ind.compute_fitness(self.fitness_calc)
            self.population.append(ind)
        self.population.sort(key=lambda x: x.fitness, reverse=True)
        self.best_individual = copy.deepcopy(self.population[0])

    def evolve_generation(self):
        new_population = []
        
        # Elitism
        elitism_count = self.params.get('elitism', 1)
        new_population.extend(copy.deepcopy(self.population[:elitism_count]))
        
        # Reproduksi
        while len(new_population) < self.params['pop_size']:
            parent1 = ops.tournament_selection(self.population)
            parent2 = ops.tournament_selection(self.population)
            
            child1, child2 = ops.crossover(parent1, parent2, self.params['crossover_rate'])
            
            # Mutasi Random
            ops.mutation(child1, self.slots, self.rooms, self.candidates, self.pref_info, self.params['mutation_rate'])
            ops.mutation(child2, self.slots, self.rooms, self.candidates, self.pref_info, self.params['mutation_rate'])
            
            # --- MEMETIC ALGORITHM UPGRADE ---
            
            # LANGKAH 1: REPAIR KONFLIK (Hilangkan Tabrakan Ruang/Dosen)
            # Kita pass all_slots dan all_rooms agar dia bisa pindah-pindah jam
            self.ls_engine.resolve_conflicts(child1, self.slots, self.rooms)
            self.ls_engine.resolve_conflicts(child2, self.slots, self.rooms)
            
            # LANGKAH 2: LOAD BALANCING (Ratakan SKS dengan Aman)
            self.ls_engine.apply_load_balancing(child1)
            self.ls_engine.apply_load_balancing(child2)
            
            # Hitung Fitness Akhir
            child1.compute_fitness(self.fitness_calc)
            child2.compute_fitness(self.fitness_calc)
            
            new_population.append(child1)
            if len(new_population) < self.params['pop_size']:
                new_population.append(child2)
                
        new_population.sort(key=lambda x: x.fitness, reverse=True)
        self.population = new_population
        
        if new_population[0].fitness > self.best_individual.fitness:
            self.best_individual = copy.deepcopy(new_population[0])

    def run(self):
        self.initialize_population()
        max_gen = self.params['max_generations']
        
        print(f"\n🚀 Memulai Evolusi MA (Load Balancing Enabled) - {max_gen} Gen")
        print("-" * 60)
        
        for generation in range(1, max_gen + 1):
            self.evolve_generation()
            
            best_now = self.population[0]
            
            if generation % 10 == 0 or best_now.fitness >= 0.999:
                conflict_count = len(best_now.conflicts)
                # Tampilkan info Fitness
                print(f"Gen {generation:3} | Konflik: {conflict_count:3} | Fit: {best_now.fitness:.5f}")
                
            if best_now.fitness >= 0.9999:
                print("\n🎉 SOLUSI OPTIMAL DITEMUKAN!")
                break
                
        return self.best_individual