option solver '../PoliMi/1sem_2y/FOR/lab/ampl/./cplex';

# SET
param n;
set H := 1..n; # set of houses

# PARAMS
param Cx{H} integer;
param Cy{H} integer;
param Dc{H} integer;
param usable{H} binary;
param range;
param max_minimart integer;

# not needed params
param Vc integer;			
param Fc integer;			
param capacity integer;	

param distance{h1 in H, h2 in H} := sqrt((Cx[h1] - Cx[h2]) ^ 2 + (Cy[h1] - Cy[h2]) ^ 2);

# AUXILIARY SET
# R is the set containing all the couples of houses that are distant less than range param
set R := setof{h1 in H, h2 in H: distance[h1, h2] <= range} (h1, h2);

# VARS
var x{H} binary;    # x[h] = 1 --> minimarket built at house i, x[h] = 0 otherwise
                
# OBJ FUNCTION
minimize obj:
    sum{h in H} (Dc[h] * x[h]);

# CONSTRAINTS
s.t. building_on_usable{h in H}:
    x[h] <= usable[h];

s.t. is_reached{h1 in H}:
    sum{(h1, h2) in R} x[h2] >= 1;

s.t. maximum_number_minimarket:
    sum{h in H} (x[h]) = max_minimart;
    
s.t. slot_1:
    x[1] = 1;
