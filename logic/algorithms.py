"""Algoritmos de rutas escolares (coordenadas euclidianas simuladas)."""
import math
import time
from functools import lru_cache

DEPOT = {"id": "D", "name": "Centro de acopio", "x": 0.0, "y": 0.0}
DEFAULT_PRODUCERS = [
    {"id":"C1", "name":"El Naranjal", "municipio":"Lérida", "weight":30, "priority":"Alta", "x":2, "y":3},
    {"id":"C2", "name":"La Esperanza", "municipio":"Ambalema", "weight":25, "priority":"Media", "x":5, "y":2},
    {"id":"C3", "name":"El Porvenir", "municipio":"Venadillo", "weight":35, "priority":"Alta", "x":6, "y":6},
    {"id":"C4", "name":"Las Palmas", "municipio":"Armero", "weight":20, "priority":"Media", "x":1, "y":7},
    {"id":"C5", "name":"San Miguel", "municipio":"Lérida", "weight":40, "priority":"Alta", "x":8, "y":3},
    {"id":"C6", "name":"La Primavera", "municipio":"Ambalema", "weight":30, "priority":"Alta", "x":4, "y":8},
]


def dist(a, b):
    return math.hypot(a["x"]-b["x"], a["y"]-b["y"])


def merge_sort(items, key):
    """Divide y Vencerás: O(n log n), orden estable."""
    if len(items) <= 1:
        return list(items)
    mid = len(items)//2
    left = merge_sort(items[:mid], key)
    right = merge_sort(items[mid:], key)
    i = j = 0
    result = []
    while i < len(left) and j < len(right):
        if key(left[i]) <= key(right[j]):
            result.append(left[i]); i += 1
        else:
            result.append(right[j]); j += 1
    return result + left[i:] + right[j:]


def subset_sum_assignment(producers, capacities):
    """DP de subconjuntos: recupera una distribución viable, la más equilibrada."""
    total = sum(int(p['weight']) for p in producers)
    c1, c2 = capacities
    reachable = {0: 0}  # suma -> máscara de productores
    for i, p in enumerate(producers):
        w = int(p['weight'])
        for s, mask in list(reachable.items()):
            if s + w <= c1 and s + w not in reachable:
                reachable[s + w] = mask | (1 << i)
    feasible = [(abs(s-(total-s)), s, mask) for s, mask in reachable.items() if total-s <= c2]
    if not feasible:
        return None
    _, s, mask = min(feasible)
    return [[p['id'] for i, p in enumerate(producers) if mask & (1<<i)],
            [p['id'] for i, p in enumerate(producers) if not mask & (1<<i)]]


def can_pack_remaining(weights, remaining_caps):
    """Comprueba que los productores pendientes caben sin dividir sus cargas."""
    total = sum(weights)
    a, b = remaining_caps
    if total > a+b or min(a,b) < 0:
        return False
    reachable = {0}
    for w in weights:
        reachable |= {s+w for s in reachable if s+w <= a}
    return any(total-s <= b for s in reachable)


def route_distance(ids, lookup):
    points = [DEPOT] + [lookup[x] for x in ids] + [DEPOT]
    return sum(dist(points[i], points[i+1]) for i in range(len(points)-1))


def nearest_route(ids, lookup):
    remaining = set(ids)
    route = []
    current = DEPOT
    while remaining:
        node = min(remaining, key=lambda pid:(dist(current, lookup[pid]), pid))
        route.append(node); remaining.remove(node)
        current = lookup[node]
    return route


def greedy(producers, capacities):
    """Vecino más cercano factible entre ambos camiones, con mirada adelante por DP."""
    lookup = {p['id']:p for p in producers}
    pending = set(lookup)
    loads = [0, 0]
    routes = [[], []]
    current = [DEPOT, DEPOT]
    while pending:
        candidates = []
        for truck in (0, 1):
            for pid in pending:
                p = lookup[pid]
                if loads[truck] + p['weight'] > capacities[truck]:
                    continue
                new_loads = list(loads); new_loads[truck] += p['weight']
                remaining = [lookup[k]['weight'] for k in pending if k != pid]
                remain_caps = [capacities[i]-new_loads[i] for i in (0,1)]
                if can_pack_remaining(remaining, remain_caps):
                    candidates.append((dist(current[truck],p), truck, pid))
        if not candidates:
            return None
        _, truck, pid = min(candidates)
        routes[truck].append(pid)
        current[truck] = lookup[pid]
        loads[truck] += lookup[pid]['weight']
        pending.remove(pid)
    return routes


def exact_backtracking(producers, capacities, upper_bound=None):
    """Backtracking con poda por capacidad, distancia y simetría de particiones.

    Para cada asignación válida, optimiza el orden mediante una búsqueda recursiva
    con cota admisible (distancia parcial + MST + conexiones a extremos).
    Cuando no vence el límite temporal, devuelve una solución global óptima.
    """
    start = time.perf_counter()
    lookup = {p['id']:p for p in producers}
    ids = [p['id'] for p in producers]
    weights = [int(p['weight']) for p in producers]
    c1,c2 = capacities
    symmetric = (c1 == c2)
    stats = {"assignment_nodes":0,"assignment_prunes_capacity":0,
             "route_nodes":0,"route_prunes_distance":0,"partitions":0}
    best_distance = float('inf')
    best_routes = None
    if upper_bound is not None:
        best_routes = [list(r) for r in upper_bound]
        best_distance = sum(route_distance(r,lookup) for r in best_routes)

    @lru_cache(None)
    def mst(subset):
        """Costo árbol de expansión mínima para los productores indicados."""
        if len(subset) <= 1: return 0.0
        todo = set(subset); first = next(iter(todo)); todo.remove(first)
        visited = {first}; total = 0.0
        while todo:
            cost, node = min((dist(lookup[u],lookup[v]),v) for u in visited for v in todo)
            total += cost; visited.add(node); todo.remove(node)
        return total

    route_cache = {}
    def optimize_route(subset):
        subset = tuple(sorted(subset))
        if subset in route_cache: return route_cache[subset]
        if not subset:
            route_cache[subset] = (0.0, [])
            return route_cache[subset]
        initial = nearest_route(subset,lookup)
        best = route_distance(initial,lookup)
        best_path = initial
        def dfs(current, remain, path, cost):
            nonlocal best,best_path
            stats['route_nodes'] += 1
            if not remain:
                full = cost + dist(current,DEPOT)
                if full < best - 1e-10:
                    best = full; best_path = path[:]
                return
            # cota optimista: conexiones más cortas desde extremo actual y depósito + MST
            lower = cost + mst(tuple(sorted(remain))) + min(dist(current,lookup[x]) for x in remain) + min(dist(DEPOT,lookup[x]) for x in remain)
            if lower >= best - 1e-10:
                stats['route_prunes_distance'] += 1
                return
            for pid in sorted(remain,key=lambda x:dist(current,lookup[x])):
                dfs(lookup[pid], remain-{pid}, path+[pid], cost+dist(current,lookup[pid]))
        dfs(DEPOT,set(subset),[],0.0)
        route_cache[subset] = (best,best_path)
        return route_cache[subset]

    assigned = [[], []]
    loads = [0,0]
    def assign(i):
        nonlocal best_distance,best_routes
        stats['assignment_nodes'] += 1
        if i == len(ids):
            stats['partitions'] += 1
            d1,r1 = optimize_route(assigned[0])
            if d1 >= best_distance-1e-10:
                stats['route_prunes_distance'] += 1
                return
            d2,r2 = optimize_route(assigned[1])
            total = d1+d2
            if total < best_distance-1e-10:
                best_distance = total; best_routes = [list(r1),list(r2)]
            return
        pid, w = ids[i], weights[i]
        # Con capacidades iguales, ancla el primer productor al camión 1
        # (intercambiar camiones produce una solución equivalente).
        options = (0,) if symmetric and i==0 else (0,1)
        for t in options:
            if loads[t]+w>capacities[t]:
                stats['assignment_prunes_capacity']+=1
                continue
            loads[t]+=w; assigned[t].append(pid)
            if can_pack_remaining(weights[i+1:], [capacities[j]-loads[j] for j in (0,1)]):
                assign(i+1)
            else:
                stats['assignment_prunes_capacity']+=1
            assigned[t].pop(); loads[t]-=w
    assign(0)
    stats['elapsed_ms'] = round((time.perf_counter()-start)*1000,3)
    stats['route_subsets_evaluated'] = len(route_cache)
    return best_routes,stats


def describe_solution(routes, producers, capacities):
    if routes is None: return None
    lookup={p['id']:p for p in producers}
    trucks=[]
    for i, route in enumerate(routes):
        load=sum(lookup[x]['weight'] for x in route)
        trucks.append({"truck":i+1,"route":["D"]+route+["D"],
                       "load":load,"capacity":capacities[i],
                       "distance":round(route_distance(route,lookup),4)})
    return {"trucks":trucks,"total_distance":round(sum(x['distance'] for x in trucks),4),
            "total_load":sum(x['load'] for x in trucks)}


def validate_producers(producers, capacities):
    if not isinstance(producers,list) or not 1 <= len(producers) <= 8:
        raise ValueError('Debe haber entre 1 y 8 productores.')
    if not isinstance(capacities,list) or len(capacities)!=2 or any(type(x)!=int or x<1 or x>100000 for x in capacities):
        raise ValueError('Indica dos capacidades enteras positivas.')
    ids=set()
    cleaned=[]
    for p in producers:
        if not isinstance(p,dict): raise ValueError('Productor inválido.')
        pid=str(p.get('id','')).strip().upper()
        if not pid or pid=='D' or len(pid)>12 or not pid.isalnum() or pid in ids:
            raise ValueError('Los códigos deben ser únicos, alfanuméricos y distintos de D.')
        ids.add(pid)
        try:
            weight=int(p['weight']); x=float(p['x']); y=float(p['y'])
        except (KeyError,ValueError,TypeError,OverflowError) as exc:
            raise ValueError(f'Datos numéricos inválidos para {pid}.') from exc
        if weight<=0 or weight>100000 or not all(math.isfinite(z) and abs(z)<=1e5 for z in (x,y)):
            raise ValueError(f'Peso o coordenadas fuera de rango para {pid}.')
        cleaned.append({"id":pid,"name":str(p.get('name',pid))[:80],
            "municipio":str(p.get('municipio',''))[:80],
            "priority":str(p.get('priority','Media'))[:30],
            "weight":weight,"x":x,"y":y})
    return cleaned


def solve(producers=None, capacities=None):
    if producers is None: producers=DEFAULT_PRODUCERS
    if capacities is None: capacities=[100,100]
    producers=validate_producers(producers,capacities)
    started=time.perf_counter()
    ordered=merge_sort(producers,key=lambda p:(dist(DEPOT,p),p['id']))
    dp=subset_sum_assignment(producers,capacities)
    if dp is None:
        return {"feasible":False,"message":"No existe una distribución que respete la capacidad individual de los camiones.",
                "producers":producers,"capacities":capacities,"ordered_ids":[p['id'] for p in ordered]}
    greedy_routes=greedy(producers,capacities)
    dp_routes=[nearest_route(group,{p['id']:p for p in producers}) for group in dp]
    exact_routes,stats=exact_backtracking(producers,capacities,greedy_routes)
    exact=describe_solution(exact_routes,producers,capacities)
    greedy_result=describe_solution(greedy_routes,producers,capacities)
    dp_result=describe_solution(dp_routes,producers,capacities)
    stats['total_elapsed_ms']=round((time.perf_counter()-started)*1000,3)
    return {"feasible":True,"producers":producers,"capacities":capacities,
            "ordered_ids":[p['id'] for p in ordered],"greedy":greedy_result,
            "dp":dp_result,"exact":exact,"stats":stats,"optimal":True,
            "greedy_gap_pct":round((greedy_result['total_distance']/exact['total_distance']-1)*100,2) if exact['total_distance'] else 0,
            "notes":["Distancias euclidianas en coordenadas simuladas; no representan carreteras reales.",
                     "Prioridades informativas; no son una restricción en esta versión.",
                     "La solución exacta minimiza distancia total respetando carga y visitas únicas."]}
