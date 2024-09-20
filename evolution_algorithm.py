import random
import time

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
        fitness_list=[(indiv, 0) for indiv in cur_gen]
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

            for rang in individual_ranges:
                if rang[1][0] <= rnd <= rang[1][1]:
                    fitness_list[individual_ranges[0]][1] += 1 # increment fitness score of drawn indiv
        
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
        

    def selection(self, cur_gen):
        selected_indivs=[]
        parents=[]
        fitness_list = self.evaluation(cur_gen)
        max_population = self.settings.get("max_population")
        score_to_survive = self.settings.get("score_to_survive")
        fitness_list[:] = [indiv for indiv in fitness_list if indiv[1] >= score_to_survive] # remove indivs below treshold
        
        # Tournament-based selection of parents
        score_to_reproduce = self.settings.get("score_to_reproduce")
        fitness_list = sorted(fitness_list, key=lambda x: x[1], reverse=True)
        for indiv in [fertile_indiv for fertile_indiv in fitness_list if fertile_indiv[1] >= score_to_reproduce]:
            parents.append(indiv)

        fitness_list = self.crossover(parents)

        # trim to max population
        if len(fitness_list) > max_population:
            fitness_list = fitness_list[:max_population]

        # convert from score tuples to just indivs
        for i in fitness_list:
            selected_indivs.append(i[0])
        
        return selected_indivs


    def crossover(self, fit_parents):
        crossover_points_gene = self.settings.get("crossover_points_gene")
        crossover_points = []
        children=[]
        children_count = self.settings.get("gen_population") - self.settings.get("selection_treshold")

        if children_count < 1:
            return fit_parents

        for i in range(children_count):
            crossover_points = random.sample(range(1,len(fit_parents[0])), crossover_points_count)
            crossover_points.sort()

            foo_parent, bar_parent = random.sample(fit_parents,2)
            use_foo_parent = True
            prev_point=0
            child=[]

            for point in crossover_points + [len(foo_parent)]:
                if use_foo_parent:
                    child.extend(foo_parent[prev_point:point])
                else:
                    child.extend(bar_parent[prev_point:point])
                
                use_foo_parent = not use_foo_parent
                prev_point = point

            children.append(child)

        new_gen = fit_parents + children
        return new_gen


    def mutation(self, generation):
        for indiv in generation:
            mut_chance = indiv[3] / 10000 # indiv[3] is mutation_chance_gene
            if not 0 <= mut_chance < 1:
                return generation
            
            mutation_factor = indiv[4] / 100 # indiv[3] is mutation_factor_gene

            if random.random() < mut_chance:
                rand_gene = indiv[random.randint(0, len(indiv) - 1)]
                if random.random() < 0.5:
                    rand_gene += mutation_factor
                else:
                    rand_gene = abs(rand_gene - mutation_factor) # avoid negative gene scores
                
        return generation


    def get_new_gen(self, cur_gen):
        new_gen = self.selection(cur_gen) # includes crossover
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
                print(f"{round(i / max_iterations,2):.2f}% | {round(time.time() - start_time, 2):.2f}s | Population: {len(cur_gen)}")

            new_gen = self.get_new_gen([ind[:] for ind in cur_gen])
            
            cur_gen = [ind[:] for ind in new_gen]

        print(f"Total run time: {round(time.time() - start_time, 4):.4f}s")
        if self.settings.get("print_final_gen"):
            for ind in sorted(cur_gen, key=sum, reverse=True):
                print(ind, sum(ind))
        
