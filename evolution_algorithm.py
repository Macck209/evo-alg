import random
import time

class EvolutionAlgorithm():
    def __init__(self, settings: dict):
        self.settings = settings

    def init_firts_gen(self):
        cur_gen=[]
        gene_count = self.settings.get("genes_per_indiv")

        for i in range(self.settings.get("gen_population")):
            individual = [random.randint(0,1) for j in range(gene_count)]
            cur_gen.append(individual)
        
        return cur_gen


    def evaluation(self, individual):
        score=sum(individual)
        penalty=0

        for i in individual:
            if i not in range(0,2):
                penalty+=100

        return score - penalty
        

    def selection(self, cur_gen):
        fitness_list=[]
        selected_indivs=[]
        for indiv in cur_gen:
            fitness_list.append((indiv, self.evaluation(indiv)))
        
        # Tournament-based selection
        if self.settings.get("selection_method") == "tournament":
            fitness_list = sorted(fitness_list, key=lambda x: x[1], reverse=True)
            for i in range(self.settings.get("selection_treshold")):
                # if you mess up config settings TODO test it
                if i >= self.settings.get("gen_population"):
                    return selected_indivs
                
                selected_indivs.append(fitness_list[i][0])
            
            return selected_indivs
        
        # Roulette-wheel selection
        cumulative_range=0
        individual_ranges=[]

        # Equation can be edited in config
        config_equation = self.settings.get("roulette_weight_func")

        for indiv in fitness_list:
            n=indiv[1]
            individual_ranges.append((indiv[0], (cumulative_range+1, cumulative_range + eval(config_equation))))
            cumulative_range += eval(config_equation)

        while len(selected_indivs) < self.settings.get("selection_treshold"):
            rand = random.randint(1, cumulative_range-1)

            for rang in individual_ranges:
                if rang[1][0] <= rand <= rang[1][1]:
                    if rang[0] not in selected_indivs:
                        selected_indivs.append(rang[0])
        
        return selected_indivs


    def mutation(self, generation):
        mutation_step_size = self.settings.get("mutation_step_size") # Num of mutated bits
        inverted_mut_chance = int(1 / self.settings.get("mutation_chance"))

        for indiv in generation:
            rand = random.randint(1, inverted_mut_chance)
            if rand==1:
                genome_len = len(indiv) - 1
                for i in range(mutation_step_size):
                    rand_gene = indiv[random.randint(0, genome_len)]
                    indiv[random.randint(0, genome_len)] = 0 if rand_gene == 1 else 1

        return generation


    def crossover(self, fit_parents):
        crossover_points_count = self.settings.get("crossover_points")
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


    def get_new_gen(self, cur_gen):
        fit_parents = self.selection(cur_gen)

        # Creating new gen
        fit_parents = self.crossover(fit_parents)
        fit_parents = self.mutation(fit_parents)
        return fit_parents


    def get_gen_score(self, cur_gen):
        foo = [self.evaluation(individual) for individual in cur_gen]
        return sum(foo)
    
    
    def simulate(self):
        start_time = time.time()
        convergence_criteria = self.settings.get("convergence_criteria")
        convergence_counter = convergence_criteria
        max_iterations = self.settings.get("max_iterations")
        print_updates = self.settings.get("print_updates")
        update_step_perc = self.settings.get("update_step_perc")
        update_step = int(update_step_perc * max_iterations)

        cur_gen = self.init_firts_gen()
        cur_total_fitness = self.get_gen_score(cur_gen)

        for i in range(max_iterations):
            if print_updates and not i % update_step:
                print(f"{round(i / max_iterations,2):.2f}% | {round(time.time() - start_time, 2):.2f}s | Cur. best: {cur_total_fitness}")

            if convergence_counter < 0:
                print(f"Break point reached. Gen nr. {i}")
                break

            new_gen = self.get_new_gen([ind[:] for ind in cur_gen])
            new_total_fitness = self.get_gen_score(new_gen)

            if new_total_fitness <= cur_total_fitness:
                convergence_counter -= 1
                continue
            
            convergence_counter = convergence_criteria
            cur_gen = [ind[:] for ind in new_gen]
            cur_total_fitness = new_total_fitness

        print(f"Total run time: {round(time.time() - start_time, 4):.4f}s | Score: {cur_total_fitness}")
        if self.settings.get("print_final_gen"):
            for ind in sorted(cur_gen, key=sum, reverse=True):
                print(ind, sum(ind))
        
