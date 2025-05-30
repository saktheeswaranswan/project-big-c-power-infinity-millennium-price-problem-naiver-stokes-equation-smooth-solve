# -*- coding: utf-8 -*-
"""1-million-dollar-price-symbolic-numeric.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/10fgCglKFlflF2CWHC0awRJBvaloxIkUj
"""

!pip install sympy numpy
!python navier_stokes_random.py

import sympy as sp
import numpy as np
import csv
import random
import os
from datetime import datetime

# Define symbols
t, x, y, z = sp.symbols('t x y z')
Re = sp.symbols('Re', positive=True)
Re_val = 100  # Example Reynolds number

# Basis functions pool (sin, cos, exp, polynomials)
def basis_funcs(var):
    return [
        sp.sin(sp.pi * var),
        sp.cos(sp.pi * var),
        sp.exp(-var),
        var,
        var**2,
        1
    ]

# Generate a random smooth function as sum of products of basis funcs over variables
def random_func(vars, max_terms=4):
    expr = 0
    for _ in range(random.randint(1, max_terms)):
        coeff = random.uniform(-2, 2)
        term = coeff
        for var in vars:
            f = random.choice(basis_funcs(var))
            term *= f
        expr += term
    return expr

# Prepare grid for numerical evaluation
N = 10
xx = np.linspace(0, 1, N)
yy = np.linspace(0, 1, N)
zz = np.linspace(0, 1, N)
tt = 0  # Fixed time for evaluation

# Create output directory with timestamp
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_dir = f'navier_stokes_output_{timestamp}'
os.makedirs(output_dir, exist_ok=True)

# Number of functions to generate
num_functions = 10000

for func_idx in range(1, num_functions + 1):
    # Generate u, v, w, p expressions
    vars_space = [x, y, z]
    vars_all = [x, y, z, t]

    u_expr = random_func(vars_space)
    v_expr = random_func(vars_space)
    w_expr = random_func(vars_space)
    p_expr = random_func(vars_all, max_terms=3)

    # Compute partial derivatives for residuals
    du_dt = sp.diff(u_expr, t)
    du_dx = sp.diff(u_expr, x)
    du_dy = sp.diff(u_expr, y)
    du_dz = sp.diff(u_expr, z)
    d2u_dx2 = sp.diff(u_expr, x, 2)
    d2u_dy2 = sp.diff(u_expr, y, 2)
    d2u_dz2 = sp.diff(u_expr, z, 2)

    dv_dt = sp.diff(v_expr, t)
    dv_dx = sp.diff(v_expr, x)
    dv_dy = sp.diff(v_expr, y)
    dv_dz = sp.diff(v_expr, z)
    d2v_dx2 = sp.diff(v_expr, x, 2)
    d2v_dy2 = sp.diff(v_expr, y, 2)
    d2v_dz2 = sp.diff(v_expr, z, 2)

    dw_dt = sp.diff(w_expr, t)
    dw_dx = sp.diff(w_expr, x)
    dw_dy = sp.diff(w_expr, y)
    dw_dz = sp.diff(w_expr, z)
    d2w_dx2 = sp.diff(w_expr, x, 2)
    d2w_dy2 = sp.diff(w_expr, y, 2)
    d2w_dz2 = sp.diff(w_expr, z, 2)

    dp_dx = sp.diff(p_expr, x)
    dp_dy = sp.diff(p_expr, y)
    dp_dz = sp.diff(p_expr, z)

    # Define residuals
    res_u = du_dt + u_expr * du_dx + v_expr * du_dy + w_expr * du_dz + dp_dx - (1/Re) * (d2u_dx2 + d2u_dy2 + d2u_dz2)
    res_v = dv_dt + u_expr * dv_dx + v_expr * dv_dy + w_expr * dv_dz + dp_dy - (1/Re) * (d2v_dx2 + d2v_dy2 + d2v_dz2)
    res_w = dw_dt + u_expr * dw_dx + v_expr * dw_dy + w_expr * dw_dz + dp_dz - (1/Re) * (d2w_dx2 + d2w_dy2 + d2w_dz2)

    # Lambdify expressions for numerical evaluation
    try:
        res_u_num = sp.lambdify((x, y, z, t), res_u.subs(Re, Re_val), 'numpy')
        res_v_num = sp.lambdify((x, y, z, t), res_v.subs(Re, Re_val), 'numpy')
        res_w_num = sp.lambdify((x, y, z, t), res_w.subs(Re, Re_val), 'numpy')

        u_num = sp.lambdify((x, y, z), u_expr, 'numpy')
        v_num = sp.lambdify((x, y, z), v_expr, 'numpy')
        w_num = sp.lambdify((x, y, z), w_expr, 'numpy')
        p_num = sp.lambdify((x, y, z, t), p_expr, 'numpy')
    except Exception as e:
        print(f"Error in lambdify for function {func_idx}: {e}")
        continue

    # Collect data rows
    data_rows = []
    residuals = []

    for xi in xx:
        for yi in yy:
            for zi in zz:
                try:
                    u_val = u_num(xi, yi, zi)
                    v_val = v_num(xi, yi, zi)
                    w_val = w_num(xi, yi, zi)
                    p_val = p_num(xi, yi, zi, tt)

                    ru = res_u_num(xi, yi, zi, tt)
                    rv = res_v_num(xi, yi, zi, tt)
                    rw = res_w_num(xi, yi, zi, tt)

                    res_norm = np.sqrt(ru**2 + rv**2 + rw**2)
                    residuals.append(res_norm)

                    data_rows.append([xi, yi, zi, u_val, v_val, w_val, p_val, ru, rv, rw, res_norm])
                except Exception as e:
                    print(f"Error in numerical evaluation at point ({xi}, {yi}, {zi}) for function {func_idx}: {e}")
                    continue

    # Write velocity, pressure, residual data to CSV
    data_filename = os.path.join(output_dir, f'navier_stokes_data_{func_idx}.csv')
    with open(data_filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['x', 'y', 'z', 'u', 'v', 'w', 'p', 'res_u', 'res_v', 'res_w', 'res_norm'])
        writer.writerows(data_rows)

    # Write summary stats of residuals
    residuals = np.array(residuals)
    summary = [
        ['Residual Norm', 'Min', 'Max', 'Mean'],
        ['res_norm', np.min(residuals), np.max(residuals), np.mean(residuals)]
    ]

    stats_filename = os.path.join(output_dir, f'navier_stokes_residual_stats_{func_idx}.csv')
    with open(stats_filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(summary)

    # Export the generated functions to CSV (string expressions)
    functions_filename = os.path.join(output_dir, f'navier_stokes_functions_{func_idx}.csv')
    with open(functions_filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Function', 'Expression'])
        writer.writerow(['u(x,y,z)', str(u_expr)])
        writer.writerow(['v(x,y,z)', str(v_expr)])
        writer.writerow(['w(x,y,z)', str(w_expr)])
        writer.writerow(['p(x,y,z,t)', str(p_expr)])

    print(f"Function {func_idx} processed and data exported.")

print(f"All {num_functions} functions processed. Data saved in '{output_dir}' directory.")

import sympy as sp
import numpy as np
import csv
import random
import os
from datetime import datetime

# Define symbols
t, x, y, z = sp.symbols('t x y z')
Re = sp.symbols('Re', positive=True)
Re_val = 100  # Example Reynolds number

# Basis functions pool (sin, cos, exp, polynomials)
def basis_funcs(var):
    return [
        sp.sin(sp.pi * var),
        sp.cos(sp.pi * var),
        sp.exp(-var),
        var,
        var**2,
        1
    ]

# Generate a random smooth function as sum of products of basis funcs over variables
def random_func(vars, max_terms=4):
    expr = 0
    for _ in range(random.randint(1, max_terms)):
        coeff = random.uniform(-2, 2)
        term = coeff
        for var in vars:
            f = random.choice(basis_funcs(var))
            term *= f
        expr += term
    return expr

# Prepare grid for numerical evaluation
N = 10
xx = np.linspace(0, 1, N)
yy = np.linspace(0, 1, N)
zz = np.linspace(0, 1, N)
tt = 0  # Fixed time for evaluation

# Create output directory with timestamp
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_dir = f'navier_stokes_output_{timestamp}'
os.makedirs(output_dir, exist_ok=True)

# Number of functions to generate
num_functions = 10000

for func_idx in range(1, num_functions + 1):
    # Generate u, v, w, p expressions
    vars_space = [x, y, z]
    vars_all = [x, y, z, t]

    u_expr = random_func(vars_space)
    v_expr = random_func(vars_space)
    w_expr = random_func(vars_space)
    p_expr = random_func(vars_all, max_terms=3)

    # Compute partial derivatives for residuals
    du_dt = sp.diff(u_expr, t)
    du_dx = sp.diff(u_expr, x)
    du_dy = sp.diff(u_expr, y)
    du_dz = sp.diff(u_expr, z)
    d2u_dx2 = sp.diff(u_expr, x, 2)
    d2u_dy2 = sp.diff(u_expr, y, 2)
    d2u_dz2 = sp.diff(u_expr, z, 2)

    dv_dt = sp.diff(v_expr, t)
    dv_dx = sp.diff(v_expr, x)
    dv_dy = sp.diff(v_expr, y)
    dv_dz = sp.diff(v_expr, z)
    d2v_dx2 = sp.diff(v_expr, x, 2)
    d2v_dy2 = sp.diff(v_expr, y, 2)
    d2v_dz2 = sp.diff(v_expr, z, 2)

    dw_dt = sp.diff(w_expr, t)
    dw_dx = sp.diff(w_expr, x)
    dw_dy = sp.diff(w_expr, y)
    dw_dz = sp.diff(w_expr, z)
    d2w_dx2 = sp.diff(w_expr, x, 2)
    d2w_dy2 = sp.diff(w_expr, y, 2)
    d2w_dz2 = sp.diff(w_expr, z, 2)

    dp_dx = sp.diff(p_expr, x)
    dp_dy = sp.diff(p_expr, y)
    dp_dz = sp.diff(p_expr, z)

    # Define residuals
    res_u = du_dt + u_expr * du_dx + v_expr * du_dy + w_expr * du_dz + dp_dx - (1/Re) * (d2u_dx2 + d2u_dy2 + d2u_dz2)
    res_v = dv_dt + u_expr * dv_dx + v_expr * dv_dy + w_expr * dv_dz + dp_dy - (1/Re) * (d2v_dx2 + d2v_dy2 + d2v_dz2)
    res_w = dw_dt + u_expr * dw_dx + v_expr * dw_dy + w_expr * dw_dz + dp_dz - (1/Re) * (d2w_dx2 + d2w_dy2 + d2w_dz2)

    # Lambdify expressions for numerical evaluation
    try:
        res_u_num = sp.lambdify((x, y, z, t), res_u.subs(Re, Re_val), 'numpy')
        res_v_num = sp.lambdify((x, y, z, t), res_v.subs(Re, Re_val), 'numpy')
        res_w_num = sp.lambdify((x, y, z, t), res_w.subs(Re, Re_val), 'numpy')

        u_num = sp.lambdify((x, y, z), u_expr, 'numpy')
        v_num = sp.lambdify((x, y, z), v_expr, 'numpy')
        w_num = sp.lambdify((x, y, z), w_expr, 'numpy')
        p_num = sp.lambdify((x, y, z, t), p_expr, 'numpy')
    except Exception as e:
        print(f"Error in lambdify for function {func_idx}: {e}")
        continue

    # Collect data rows
    data_rows = []
    residuals = []

    for xi in xx:
        for yi in yy:
            for zi in zz:
                try:
                    u_val = u_num(xi, yi, zi)
                    v_val = v_num(xi, yi, zi)
                    w_val = w_num(xi, yi, zi)
                    p_val = p_num(xi, yi, zi, tt)

                    ru = res_u_num(xi, yi, zi, tt)
                    rv = res_v_num(xi, yi, zi, tt)
                    rw = res_w_num(xi, yi, zi, tt)

                    res_norm = np.sqrt(ru**2 + rv**2 + rw**2)
                    residuals.append(res_norm)

                    data_rows.append([xi, yi, zi, u_val, v_val, w_val, p_val, ru, rv, rw, res_norm])
                except Exception as e:
                    print(f"Error in numerical evaluation at point ({xi}, {yi}, {zi}) for function {func_idx}: {e}")
                    continue

    # Write velocity, pressure, residual data to CSV
    data_filename = os.path.join(output_dir, f'navier_stokes_data_{func_idx}.csv')
    with open(data_filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['x', 'y', 'z', 'u', 'v', 'w', 'p', 'res_u', 'res_v', 'res_w', 'res_norm'])
        writer.writerows(data_rows)

    # Write summary stats of residuals
    residuals = np.array(residuals)
    summary = [
        ['Residual Norm', 'Min', 'Max', 'Mean'],
        ['res_norm', np.min(residuals), np.max(residuals), np.mean(residuals)]
    ]

    stats_filename = os.path.join(output_dir, f'navier_stokes_residual_stats_{func_idx}.csv')
    with open(stats_filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(summary)

    # Export the generated functions to CSV (string expressions)
    functions_filename = os.path.join(output_dir, f'navier_stokes_functions_{func_idx}.csv')
    with open(functions_filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Function', 'Expression'])
        writer.writerow(['u(x,y,z)', str(u_expr)])
        writer.writerow(['v(x,y,z)', str(v_expr)])
        writer.writerow(['w(x,y,z)', str(w_expr)])
        writer.writerow(['p(x,y,z,t)', str(p_expr)])

    print(f"Function {func_idx} processed and data exported.")

print(f"All {num_functions} functions processed. Data saved in '{output_dir}' directory.")

import sympy as sp
import numpy as np
import csv
import random
import os
from datetime import datetime

# Initialize symbols
t, x, y, z = sp.symbols('t x y z')
Re = sp.symbols('Re', positive=True)
Re_val = 100  # Example Reynolds number

# Define a comprehensive pool of basis functions
def basis_funcs(var):
    return [
        sp.sin(sp.pi * var),
        sp.cos(sp.pi * var),
        sp.exp(-var),
        sp.exp(var),
        sp.log(var + 1),
        sp.sqrt(var + 1),
        sp.tan(sp.pi * var),
        sp.asin(sp.sin(sp.pi * var)),
        sp.acos(sp.cos(sp.pi * var)),
        sp.atan(sp.tan(sp.pi * var)),
        sp.sinh(var),
        sp.cosh(var),
        sp.tanh(var),
        var,
        var**2,
        var**3,
        1
    ]

# Generate a random smooth function as sum of products of basis functions over variables
def random_func(vars, max_terms=4):
    expr = 0
    for _ in range(random.randint(1, max_terms)):
        coeff = random.uniform(-2, 2)
        term = coeff
        for var in vars:
            f = random.choice(basis_funcs(var))
            term *= f
        expr += term
    return expr

# Prepare grid for numerical evaluation
N = 10
xx = np.linspace(0, 1, N)
yy = np.linspace(0, 1, N)
zz = np.linspace(0, 1, N)
tt = 0  # Fixed time for evaluation

# Create output directory with timestamp
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_dir = f'navier_stokes_output_{timestamp}'
os.makedirs(output_dir, exist_ok=True)

# Number of functions to generate
num_functions = 10000

for func_idx in range(1, num_functions + 1):
    # Generate u, v, w, p expressions
    vars_space = [x, y, z]
    vars_all = [x, y, z, t]

    u_expr = random_func(vars_space)
    v_expr = random_func(vars_space)
    w_expr = random_func(vars_space)
    p_expr = random_func(vars_all, max_terms=3)

    # Compute partial derivatives for residuals
    du_dt = sp.diff(u_expr, t)
    du_dx = sp.diff(u_expr, x)
    du_dy = sp.diff(u_expr, y)
    du_dz = sp.diff(u_expr, z)
    d2u_dx2 = sp.diff(u_expr, x, 2)
    d2u_dy2 = sp.diff(u_expr, y, 2)
    d2u_dz2 = sp.diff(u_expr, z, 2)

    dv_dt = sp.diff(v_expr, t)
    dv_dx = sp.diff(v_expr, x)
    dv_dy = sp.diff(v_expr, y)
    dv_dz = sp.diff(v_expr, z)
    d2v_dx2 = sp.diff(v_expr, x, 2)
    d2v_dy2 = sp.diff(v_expr, y, 2)
    d2v_dz2 = sp.diff(v_expr, z, 2)

    dw_dt = sp.diff(w_expr, t)
    dw_dx = sp.diff(w_expr, x)
    dw_dy = sp.diff(w_expr, y)
    dw_dz = sp.diff(w_expr, z)
    d2w_dx2 = sp.diff(w_expr, x, 2)
    d2w_dy2 = sp.diff(w_expr, y, 2)
    d2w_dz2 = sp.diff(w_expr, z, 2)

    dp_dx = sp.diff(p_expr, x)
    dp_dy = sp.diff(p_expr, y)
    dp_dz = sp.diff(p_expr, z)

    # Define residuals
    res_u = du_dt + u_expr * du_dx + v_expr * du_dy + w_expr * du_dz + dp_dx - (1/Re) * (d2u_dx2 + d2u_dy2 + d2u_dz2)
    res_v = dv_dt + u_expr * dv_dx + v_expr * dv_dy + w_expr * dv_dz + dp_dy - (1/Re) * (d2v_dx2 + d2v_dy2 + d2v_dz2)
    res_w = dw_dt + u_expr * dw_dx + v_expr * dw_dy + w_expr * dw_dz + dp_dz - (1/Re) * (d2w_dx2 + d2w_dy2 + d2w_dz2)

    # Lambdify expressions for numerical evaluation
    try:
        res_u_num = sp.lambdify((x, y, z, t), res_u.subs(Re, Re_val), 'numpy')
        res_v_num = sp.lambdify((x, y, z, t), res_v.subs(Re, Re_val), 'numpy')
        res_w_num = sp.lambdify((x, y, z, t), res_w.subs(Re, Re_val), 'numpy')

        u_num = sp.lambdify((x, y, z), u_expr, 'numpy')
        v_num = sp.lambdify((x, y, z), v_expr, 'numpy')
        w_num = sp.lambdify((x, y, z), w_expr, 'numpy')
        p_num = sp.lambdify((x, y, z, t), p_expr, 'numpy')
    except Exception as e:
        print(f"Error in lambdify for function {func_idx}: {e}")
        continue

    # Collect data rows
    data_rows = []
    residuals = []

    for xi in xx:
        for yi in yy:
            for zi in zz:
                try:
                    u_val = u_num(xi, yi, zi)
                    v_val = v_num(xi, yi, zi)
                    w_val = w_num(xi, yi, zi)
                    p_val = p_num(xi, yi, zi, tt)

                    ru = res_u_num(xi, yi, zi, tt)
                    rv = res_v_num(xi, yi, zi, tt)
                    rw = res_w_num(xi, yi, zi, tt)

                    res_norm = np.sqrt(ru**2 + rv**2 + rw**2)
                    residuals.append(res_norm)

                    data_rows.append([xi, yi, zi, u_val, v_val, w_val, p_val, ru, rv, rw, res_norm])
                except Exception as e:
                    print(f"Error in numerical evaluation at point ({xi}, {yi}, {zi}) for function {func_idx}: {e}")
                    continue

    # Write velocity, pressure, residual data to CSV
    data_filename = os.path.join(output_dir, f'navier_stokes_data_{func_idx}.csv')
    with open(data_filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['x', 'y', 'z', 'u', 'v', 'w', 'p', 'res_u', 'res_v', 'res_w', 'res_norm'])
        writer.writerows(data_rows)

    # Write summary stats of residuals
    residuals = np.array(residuals)
    summary = [
        ['Residual Norm', 'Min', 'Max', 'Mean'],
        ['res_norm', np.min(residuals), np.max(residuals), np.mean(residuals)]
    ]

    stats_filename = os.path.join(output_dir, f'navier_stokes_residual_stats_{func_idx}.csv')
    with open(stats_filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(summary)

    # Export the generated functions to CSV (string expressions)
    functions_filename = os.path.join(output_dir, f'navier_stokes_functions_{func_idx}.csv')
    with open(functions_filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Function', 'Expression'])
        writer.writerow(['u(x,y,z)', str(u_expr)])
        writer.writerow(['v(x,y,z)', str(v_expr)])
        writer.writerow(['w(x,y,z)', str(w_expr)])
        writer.writerow(['p(x,y,z,t)', str(p_expr)])

    print(f"Function {func_idx} processed and data exported.")

print(f"All {num_functions} functions processed. Data saved in '{output_dir}' directory.")