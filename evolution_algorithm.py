import random
import time
import statistics

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
            cur_gen.append(init_genome)
        
        return cur_gen


    # Roulette-wheel assignment of points based on gatherer_gene
    def food_evaluation(self, cur_gen):
        fitness_list=[[indiv, 0] for indiv in cur_gen]
        cumulative_range=0
        individual_ranges=[]
        food_left = self.settings.get("food")

        # Equation can be edited in config
        config_equation = self.settings.get("gatherer_roulette_weight_func")

        index=0
        for indiv in cur_gen:
            n=indiv[0] # n is the gatherer_gene
            individual_ranges.append((index, (cumulative_range+1, cumulative_range + eval(config_equation))))
            cumulative_range += eval(config_equation)
            index+=1

        while food_left > 0:
            rnd = random.randint(1, cumulative_range-1)

            for (index, rang) in individual_ranges:
                if rang[0] <= rnd <= rang[1]:
                    fitness_list[index][1] += 1 # increment fitness score of drawn indiv
                    food_left -= 1
        
        return fitness_list


    def fertility_evaluation(self, fitness_list):
        config_equation = self.settings.get("fertility_multiplier_func")
        for indiv in fitness_list:
            score=indiv[1]
            fert=indiv[0][1]
            indiv[1] = eval(config_equation)

        return fitness_list


    def evaluation(self, cur_gen):
        fitness_list = self.food_evaluation(cur_gen)
        fitness_list = self.fertility_evaluation(fitness_list)

        return fitness_list
        

    def parent_selection(self, cur_gen):
        selected_indivs=[]
        super_indivs=[]
        parents=[]
        fitness_list = self.evaluation(cur_gen)
        #score_to_survive = self.settings.get("score_to_survive")
        score_for_more_children = self.settings.get("score_for_more_children")
        #fitness_list[:] = [indiv for indiv in fitness_list if indiv[1] >= score_to_survive] # remove indivs below treshold
        
        # Tournament-based selection of parents
        score_to_reproduce = self.settings.get("score_to_reproduce")
        fitness_list = sorted(fitness_list, key=lambda x: x[1], reverse=True)
        for indiv in [fertile_indiv for fertile_indiv in fitness_list if fertile_indiv[1] >= score_to_reproduce]:
            parents.append(indiv)

        # convert from score tuples to just indivs
        for i in parents:
            selected_indivs.append(i[0]) #TODO clearer variable names for parents and selected_indivs
        
        # indivs whom can reproduce more than once
        for i in fitness_list:
            if i[1] > score_for_more_children:
                super_indivs.append(i[0])
        
        return selected_indivs, super_indivs


    def crossover(self, fit_parents, children: list):
        crossover_points = []
        children_count = len(fit_parents) // 2

        for i in range(children_count):
            foo_parent, bar_parent = random.sample(fit_parents,2)
            # determined by parents' crossover_points_gene. Value between 1-5
            crossover_points_num = min(len(foo_parent), max(1, int((foo_parent[2] + bar_parent[2]) / 100)))
            crossover_points = random.sample(range(1, len(fit_parents[0])), crossover_points_num)
            crossover_points.sort()

            use_foo_parent = True
            prev_point=0
            child_1, child_2 = [], []

            for point in crossover_points + [len(foo_parent)]:
                if use_foo_parent:
                    child_1.extend(foo_parent[prev_point:point])
                    child_2.extend(bar_parent[prev_point:point])
                else:
                    child_1.extend(bar_parent[prev_point:point])
                    child_2.extend(foo_parent[prev_point:point])
                
                use_foo_parent = not use_foo_parent
                prev_point = point

            child_1 = self.mutate_if_inbred(foo_parent, bar_parent, child_1)
            child_2 = self.mutate_if_inbred(foo_parent, bar_parent, child_2)

            children.append(child_1)
            children.append(child_2)

        return children


    def mutate_if_inbred(self, foo_parent, bar_parent, child):
        inbreeding_treshold = self.settings.get("inbreeding_treshold")
        similar_gene_counter=0
        for (index, gene) in enumerate(foo_parent):
            if gene == bar_parent[index]:
                similar_gene_counter += 1

        if inbreeding_treshold <= similar_gene_counter:
            mutation_factor = self.settings.get("inbreeding_mutation_factor")
            child = self.mutate_gene(child, mutation_factor)

        return child


    def mutate_gene(self, indiv, mutation_factor):
        max_gene_value = self.settings.get("max_gene_value")
        mutation_factor = random.randint(0, mutation_factor)
        rand_gene_index = random.randint(0, len(indiv) - 1)
        if random.random() < 0.5:
            indiv[rand_gene_index] += mutation_factor
        else:
            indiv[rand_gene_index] = abs(rand_gene_index - mutation_factor) # avoid negative gene scores
        
        indiv[rand_gene_index] = min(indiv[rand_gene_index], max_gene_value)

        return indiv


    def mutation(self, generation):
        for indiv in generation:
            mut_chance = min(0, max(0, indiv[3] / 1000)) # indiv[3] is mutation_chance_gene
            if not 0 <= mut_chance < 1:
                continue
            
            mutation_factor = int(indiv[4] / 10) # indiv[3] is mutation_factor_gene
            rng = random.random()

            if rng < mut_chance:
                indiv = self.mutate_gene(indiv, mutation_factor)
                
        return generation


    def get_new_gen(self, cur_gen):
        max_population = self.settings.get("max_population")

        parents, super_parents = self.parent_selection(cur_gen)

        if len(parents) < 2:
            return []

        new_gen = self.crossover(parents, [])
        new_gen = self.crossover(super_parents, new_gen)

        # trim to max population
        if len(new_gen) > max_population:
            new_gen = new_gen[:max_population]

        new_gen = self.mutation(new_gen)

        return new_gen
    
    
    def simulate(self):
        start_time = time.time()
        max_iterations = self.settings.get("max_iterations")
        print_updates = self.settings.get("print_updates")
        update_step_perc = self.settings.get("update_step_perc")
        update_step = int(update_step_perc * max_iterations)

        cur_gen = self.init_firts_gen()

        for i in range(max_iterations):
            if print_updates and not i % update_step:
                print(f"{round(100 * i / max_iterations,2):.2f}% | {round(time.time() - start_time, 2):.2f}s | Population: {len(cur_gen)}")

            if len(cur_gen) < 2:
                break

            new_gen = self.get_new_gen([ind[:] for ind in cur_gen])
            
            cur_gen = [ind[:] for ind in new_gen]

        # summary
        print(f"Total run time: {round(time.time() - start_time, 4):.4f}s | Final population: {len(cur_gen)}")

        if len(cur_gen) and self.settings.get("print_final_stats"):
            foo_list = [[j[i] for j in cur_gen] for i in range( len(cur_gen[0])) ]
            print()
            print(f"Final generation's gene values summed up:\n[{''.join([f'{sum(i)}\t' for i in foo_list])}]")
            print(f"Smallest genes:\n[{''.join([f'{min(i)}\t' for i in foo_list])}]")
            print(f"Largest genes:\n[{''.join([f'{max(i)}\t' for i in foo_list])}]")
            print(f"Mean avg:\n[{''.join([f'{round(statistics.mean(i), 2):.1f}\t' for i in foo_list])}]")
            print(f"Median avg:\n[{''.join([f"{statistics.median(i)}\t" for i in foo_list])}]")
        
        if self.settings.get("print_final_gen"):
            print('Final generation:')
            for ind in cur_gen:
                print(ind)
        
