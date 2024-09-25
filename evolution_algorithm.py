import random
import time
import statistics


class Individual():
    def __init__(self, genome=None, food_score=0, fert_score=0, age=0):
        self.genome = [i for i in genome] if genome is not None else []
        self.food_score = food_score
        self.fert_score = fert_score
        self.age = age

class EvolutionAlgorithm():
    def __init__(self, settings: dict):
        self.settings = settings


    def init_firts_gen(self):
        cur_gen=[]
        init_genome = [self.settings.get("gatherer_gene"),
                       self.settings.get("fertility_gene"),
                       self.settings.get("crossover_points_gene"),
                       self.settings.get("mutation_chance_gene"),
                       self.settings.get("mutation_factor_gene")]

        #TODO multiple groups of different species
        for i in range(self.settings.get("init_population")):
            cur_gen.append(Individual(init_genome))
        
        return cur_gen


    # Roulette-wheel assignment of points based on gatherer_gene
    def food_evaluation(self, cur_gen):
        cumulative_range=0
        individual_ranges=[]
        food_left = self.settings.get("food")
        debuff = self.settings.get("age_gatherer_debuff")

        # Equation can be edited in config
        config_equation = self.settings.get("gatherer_roulette_weight_func")

        for (index, indiv) in enumerate(cur_gen):
            indiv.food_score=0
            age=indiv.age
            n=indiv.genome[0] # n is the gatherer_gene
            individual_ranges.append((index, (cumulative_range+1, cumulative_range + eval(config_equation))))
            cumulative_range += eval(config_equation)

        while food_left > 0:
            if cumulative_range <= 1:
                return
            
            rnd = random.randint(1, cumulative_range-1)

            for (index, rang) in individual_ranges:
                if rang[0] <= rnd <= rang[1]:
                    cur_gen[index].food_score += 1 # increment food score of drawn indiv
                    food_left -= 1


    def fertility_evaluation(self, cur_gen):
        survive_to_reproduce = self.settings.get("survive_to_reproduce")
        buff = self.settings.get("age_fertility_buff")
        score_to_survive = self.settings.get("score_to_survive")
        config_equation = self.settings.get("fertility_gatherer_relation")
        for indiv in cur_gen:
            age=indiv.age
            food_score=indiv.food_score
            if survive_to_reproduce and food_score < score_to_survive:
                continue
            fert=indiv.genome[1]
            gatherer_gene=indiv.genome[0]
            indiv.fert_score = eval(config_equation)
        

    def survival_selection(self, cur_gen):
        score_to_survive = self.settings.get("score_to_survive")

        # determine food scores
        self.food_evaluation(cur_gen)

        # remove indivs below treshold
        survivors = [indiv for indiv in cur_gen if indiv.food_score >= score_to_survive].copy()

        for ind in survivors:
            ind.age += 1

        return survivors


    def parent_selection(self, cur_gen):
        super_parents=[]
        parents=[]
        
        # Tournament-based selection of parents
        score_to_reproduce = self.settings.get("score_to_reproduce")
        self.fertility_evaluation(cur_gen)
        cur_gen.sort(key=lambda x: x.fert_score, reverse=True)
        for indiv in cur_gen:
            if indiv.fert_score >= score_to_reproduce:
                new_parent = Individual(indiv.genome, indiv.food_score, indiv.fert_score, indiv.age)
                parents.append(new_parent)

        # indivs whom can reproduce more than once
        score_for_more_children = self.settings.get("score_for_more_children")
        for indiv in cur_gen:
            if indiv.fert_score > score_for_more_children:
                new_parent = Individual(indiv.genome, indiv.food_score, indiv.fert_score, indiv.age)
                super_parents.append(new_parent)
                
        return parents, super_parents


    def crossover(self, fit_parents, new_gen: list):
        crossover_points = []
        children_count = len(fit_parents) // 2

        for i in range(children_count):
            foo_parent, bar_parent = random.sample(fit_parents,2)
            # determined by parents' crossover_points_gene. Value between 1-5
            crossover_points_num = min(len(foo_parent.genome), max(1, int((foo_parent.genome[2] + bar_parent.genome[2]) / 100)))
            crossover_points = random.sample(range(1, len(fit_parents[0].genome)), min(crossover_points_num, 4))
            crossover_points.sort()

            use_foo_parent = True
            prev_point=0
            child_1 = Individual()
            child_2 = Individual()

            for point in crossover_points + [len(foo_parent.genome)]:
                if use_foo_parent:
                    child_1.genome.extend(foo_parent.genome[prev_point:point])
                    child_2.genome.extend(bar_parent.genome[prev_point:point])
                else:
                    child_1.genome.extend(bar_parent.genome[prev_point:point])
                    child_2.genome.extend(foo_parent.genome[prev_point:point])
                
                use_foo_parent = not use_foo_parent
                prev_point = point

            self.mutate_if_inbred(foo_parent, bar_parent, child_1)
            self.mutate_if_inbred(foo_parent, bar_parent, child_2)

            new_gen.append(child_1)
            new_gen.append(child_2)


    def mutate_if_inbred(self, foo_parent:Individual, bar_parent:Individual, child:Individual):
        similarity_treshold = self.settings.get("gene_similarity_treshold")
        inbreeding_treshold = self.settings.get("inbreeding_treshold")
        similar_gene_counter=0
        for (index, gene) in enumerate(foo_parent.genome):
            if gene in range(bar_parent.genome[index]-similarity_treshold, bar_parent.genome[index]+similarity_treshold):
                similar_gene_counter += 1

        if inbreeding_treshold <= similar_gene_counter:
            mutation_factor = self.settings.get("inbreeding_mutation_factor")
            self.mutate_gene(child, mutation_factor)


    def mutate_gene(self, indiv:Individual, mutation_factor):
        max_gene_value = self.settings.get("max_gene_value")
        min_gene_value = self.settings.get("min_gene_value")
        mutation_factor = random.randint(0, mutation_factor)
        rand_gene_index = random.randint(0, len(indiv.genome) - 1)
        if random.random() < 0.5:
            indiv.genome[rand_gene_index] += mutation_factor
        else:
            indiv.genome[rand_gene_index] = abs(rand_gene_index - mutation_factor) # avoid negative gene scores
        
        indiv.genome[rand_gene_index] = max(min_gene_value, min(indiv.genome[rand_gene_index], max_gene_value))


    def mutation(self, cur_gen):
        for indiv in cur_gen:
            mut_chance = indiv.genome[3] / 1000 # genome[3] is mutation_chance_gene
            if not 0 < mut_chance <= 1:
                continue
            
            mutation_factor = int(indiv.genome[4] / 10) # genome[4] is mutation_factor_gene
            rng = random.random()

            if rng < mut_chance:
                self.mutate_gene(indiv, mutation_factor)


    def get_new_gen(self, cur_gen):
        max_population = self.settings.get("max_population")

        survivors = self.survival_selection(cur_gen)
        parents, super_parents = self.parent_selection(cur_gen)

        new_gen=[]
        self.crossover(parents, new_gen)
        self.crossover(super_parents, new_gen)

        self.mutation(new_gen)

        new_gen.extend(survivors)

        if len(new_gen) < 2:
            # Show last survivor
            #TODO make always work
            print('Last survivor:',[(i.genome, i.food_score, round(i.fert_score,1), i.age) for i in new_gen])
            return []
        
        # trim to max population
        if len(new_gen) > max_population:
            new_gen = new_gen[:max_population]

        return new_gen
    
    
    def simulate(self):
        start_time = time.time()
        max_iterations = self.settings.get("max_iterations")
        print_updates = self.settings.get("print_updates")
        update_step_perc = self.settings.get("update_step_perc")
        update_step = max(1, int(update_step_perc * max_iterations))

        cur_gen = self.init_firts_gen()

        for i in range(max_iterations):
            if print_updates and not i % update_step:
                print(f"{round(100 * i / max_iterations,2):.2f}% | {round(time.time() - start_time, 2):.2f}s | Population: {len(cur_gen)}")

            if len(cur_gen) < 2:
                break

            new_gen = self.get_new_gen(cur_gen.copy())
            #print([(i.genome, i.food_score, round(i.fert_score,1)) for i in new_gen],'\n')
            cur_gen = new_gen.copy()

        # summary
        print(f"Total run time: {round(time.time() - start_time, 4):.4f}s | Final population: {len(cur_gen)}")

        if len(cur_gen) and self.settings.get("print_final_stats"):
            foo_list = [[indiv.genome[i] for indiv in cur_gen] for i in range( len(cur_gen[0].genome)) ]
            print()
            print(f"Final generation's gene values summed up:\n[{''.join([f'{sum(i)}\t' for i in foo_list])}]")
            print(f"Smallest genes:\n[{''.join([f'{min(i)}\t' for i in foo_list])}]")
            print(f"Largest genes:\n[{''.join([f'{max(i)}\t' for i in foo_list])}]")
            print(f"Mean avg:\n[{''.join([f'{round(statistics.mean(i), 2):.1f}\t' for i in foo_list])}]")
            print(f"Median avg:\n[{''.join([f"{statistics.median(i)}\t" for i in foo_list])}]")
        
        if self.settings.get("print_final_gen"):
            print('Final generation:')
            cur_gen.sort(key=lambda x: x.age, reverse=True)
            for ind in cur_gen:
                print(ind.genome, '\t', ind.food_score, '\t', round(ind.fert_score, 1), '\t', ind.age)
        
