import copy
from ga_core.individual import Individual
from ga_core.fitness import FitnessCalculator
import ga_core.operators as ops

class GeneticAlgorithm:
    def __init__(self, data, params):
        """
        Inisialisasi Mesin GA.
        :param data: Dictionary berisi classes, slots, rooms.
        :param params: Konfigurasi (pop_size, mutation_rate, dll).
        """
        self.data = data
        self.params = params
        
        # Unpack data resources
        self.classes = data['classes']
        self.slots = data['slots']
        self.rooms = data['rooms']
        
        # Siapkan Calculator
        self.fitness_calc = FitnessCalculator(self.slots, self.rooms)
        
        # State Internal
        self.population = []
        self.best_individual = None
        self.history = [] # Untuk menyimpan grafik progress fitness

    def initialize_population(self):
        """Membangun populasi awal secara acak."""
        print(">>> Inisialisasi Populasi Awal...")
        self.population = []
        for _ in range(self.params['pop_size']):
            ind = Individual(self.classes, self.slots, self.rooms)
            ind.initialize_random()
            ind.compute_fitness(self.fitness_calc)
            self.population.append(ind)
            
        # Urutkan dari fitness tertinggi
        self.population.sort(key=lambda x: x.fitness, reverse=True)
        self.best_individual = self.population[0]

    def evolve_generation(self):
        """
        Membuat satu generasi baru (The Core Loop).
        Strategi: Elitism (Simpan yang terbaik) + Generational Replacement.
        """
        new_population = []
        
        # 1. ELITISM
        # Kita simpan 1-2 individu terbaik agar solusi tidak hilang/mundur
        elitism_count = self.params.get('elitism', 1)
        new_population.extend(copy.deepcopy(self.population[:elitism_count]))
        
        # 2. REPRODUKSI
        # Loop sampai populasi penuh kembali
        while len(new_population) < self.params['pop_size']:
            # A. Seleksi Orang Tua
            parent1 = ops.tournament_selection(self.population)
            parent2 = ops.tournament_selection(self.population)
            
            # B. Crossover (Kawin Silang)
            child1, child2 = ops.crossover(
                parent1, parent2, 
                self.params['crossover_rate']
            )
            
            # C. Mutasi (Eksperimen Acak)
            ops.mutation(child1, self.slots, self.rooms, self.params['mutation_rate'])
            ops.mutation(child2, self.slots, self.rooms, self.params['mutation_rate'])
            
            # D. Hitung Fitness Anak (PENTING! Sebelum masuk populasi)
            child1.compute_fitness(self.fitness_calc)
            child2.compute_fitness(self.fitness_calc)
            
            # E. Masukkan ke Populasi Baru
            new_population.append(child1)
            # Cek overflow (biar pas ukuran populasi)
            if len(new_population) < self.params['pop_size']:
                new_population.append(child2)
                
        # 3. UPDATE POPULASI
        # Urutkan lagi agar index 0 selalu yang terbaik
        new_population.sort(key=lambda x: x.fitness, reverse=True)
        self.population = new_population
        
        # Update Global Best jika ditemukan yang lebih baik
        if new_population[0].fitness > self.best_individual.fitness:
            self.best_individual = copy.deepcopy(new_population[0])

    def run(self):
        """Jalankan simulasi penuh."""
        self.initialize_population()
        
        max_gen = self.params['max_generations']
        
        print(f"\n🚀 Memulai Evolusi ({max_gen} Generasi)")
        print(f"   Populasi: {self.params['pop_size']} | Mutasi: {self.params['mutation_rate']}")
        print("-" * 60)
        
        for generation in range(1, max_gen + 1):
            self.evolve_generation()
            
            # Logging Progress
            best_now = self.population[0]
            self.history.append(best_now.fitness)
            
            # Print setiap 10 generasi atau jika solusi sempurna ditemukan
            if generation % 10 == 0 or best_now.fitness >= 0.999:
                conflict_count = len(best_now.conflicts)
                print(f"Gen {generation:3} | Fitness: {best_now.fitness:.5f} | Konflik: {conflict_count} | (Best: {self.best_individual.fitness:.5f})")
                
            # Early Stopping (Jika sudah sempurna, berhenti)
            if best_now.fitness >= 0.9999:
                print("\n🎉 SOLUSI OPTIMAL DITEMUKAN!")
                break
                
        print("-" * 60)
        print("🏁 Selesai.")
        return self.best_individual