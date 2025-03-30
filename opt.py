import numpy as np
from scipy.optimize import minimize

# Step 1: Define the coefficients for the objective function
c = np.array([1.0, 2.0])  # Coefficients for the linear part
Q = np.array([[1.0, 0.0], [0.0, 1.0]])  # Quadratic part (identity matrix for simplicity)

# Step 2: Define the constraints
A = np.array([[1.0, 1.0], [-1.0, 2.0], [2.0, 1.0]])  # Coefficients of constraints
b = np.array([3.0, 2.0, 4.0])  # Bounds for constraints

# Step 3: Define the objective function (negative for minimization)
def objective(x):
    return - (c.T @ x) + 0.5 * (x.T @ Q @ x)  # Minimize the negative of the original function

# Step 4: Define the constraints in a form suitable for SciPy
constraints = [{'type': 'ineq', 'fun': lambda x: b - A @ x}]

# Step 5: Define bounds for the variables (if necessary)
bounds = [(0, None), (0, None)]  # Non-negative constraints on x variables

# Step 6: Provide an initial guess
x_initial = np.zeros(len(c))

# Step 7: Perform the optimization
result = minimize(objective, x_initial, method='SLSQP', bounds=bounds, constraints=constraints)

# Step 8: Output the results
if result.success:
    print("Objective Function Value:", -result.fun)  # Original objective value
    print("Optimization Variables:", result.x)  # Optimization results for variables
else:
    print("Optimization failed:", result.message)