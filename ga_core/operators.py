import random
import copy

# ============================
# 1. SELEKSI (TOURNAMENT)
# ============================
def tournament_selection(population, k=3):
    candidates = random.sample(population, k)
    best = max(candidates, key=lambda ind: ind.fitness)
    return best

# ============================
# 2. CROSSOVER (KAWIN SILANG)
# ============================
def crossover(parent1, parent2, crossover_rate=0.8):
    if random.random() > crossover_rate:
        return copy.deepcopy(parent1), copy.deepcopy(parent2)

    child1 = copy.deepcopy(parent1)
    child2 = copy.deepcopy(parent2)
    
    num_genes = len(parent1.chromosome)
    for i in range(num_genes):
        if random.random() < 0.5:
            child1.chromosome[i], child2.chromosome[i] = child2.chromosome[i], child1.chromosome[i]
            
    # Reset
    child1.fitness = 0.0
    child1.conflicts = []
    child2.fitness = 0.0
    child2.conflicts = []
    return child1, child2

# ============================
# 3. MUTATION (BACK TO BASIC + RANDOM SWAP)
# ============================
def mutation(individual, all_slots, all_rooms, candidates, pref_info, mutation_rate=0.1):
    """
    Mutasi Random untuk eksplorasi.
    Urusan Balancing dan Repair diserahkan ke Local Search (Memetic).
    """
    for gene in individual.chromosome:
        if random.random() < mutation_rate:
            
            choice = random.random()
            
            if choice < 0.4:
                # Ganti Slot
                gene['slot_id'] = random.choice(all_slots)['slot_id']
            elif choice < 0.8:
                # Ganti Ruang
                gene['room_id'] = random.choice(all_rooms)['room_id']
            else:
                # Ganti Dosen (Random Swap saja, bukan Robin Hood)
                # Biar LocalSearch yang urus balancing yang aman
                kode_mk = gene['kode_mk']
                possible = candidates.get(kode_mk, [])
                if len(possible) > 1:
                    new_dosen = random.choice(possible)
                    gene['dosen'] = new_dosen
                    info = pref_info.get((new_dosen, kode_mk), {'prioritas': 99})
                    gene['dosen_priority'] = info['prioritas']

    # Reset fitness
    individual.fitness = 0.0
    individual.conflicts = []