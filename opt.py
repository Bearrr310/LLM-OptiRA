
import numpy as np
from scipy.optimize import minimize

# Parameters
N0 = 1e-9  # noise power in W
B_max = 10  # max bandwidth in MHz
P_max = 5  # max transmit power in W
h_max = 10  # maximum channel gain

# Channel condition
X = np.random.normal(0, 1)
Y = np.random.normal(0, 1)
h = np.sqrt(X**2 + Y**2)

# Change of variable
def compute_z(P, h):
    return P * h

# Objective function
def objective(vars):
    P, B = vars
    z = compute_z(P, h)
    return -B * np.log2(1 + z / (N0 * B))  # minimize negative for maximization

# Constraints
def constraint_power(vars):
    P, B = vars
    return P_max - P  # P must be <= P_max

def constraint_bandwidth(vars):
    P, B = vars
    return B_max - B  # B must be <= B_max

def constraint_channel(vars):
    P, B = vars
    z = compute_z(P, h)
    return np.array([z, P * h_max - z])  # 0 < z <= P * h_max

# Initial guess
initial_guess = [1, 1]

# Constraints dictionary
constraints = [{'type': 'ineq', 'fun': constraint_power},
               {'type': 'ineq', 'fun': constraint_bandwidth},
               {'type': 'ineq', 'fun': constraint_channel}]

# Solve the optimization problem
result = minimize(objective, initial_guess, constraints=constraints)

# Output results
P_opt, B_opt = result.x
z_opt = compute_z(P_opt, h)
R_opt = -result.fun  # Maximize, so negate back

# Ensure positive output for the objective function
if R_opt > 0:
    print("Objective Function Value (R):", R_opt)
else:
    print("Objective Function Value (R):", 0)

print("Optimized Power (P):", P_opt)
print("Optimized Bandwidth (B):", B_opt)
print("Channel Gain (h):", h)
print("Derived z:", z_opt)
