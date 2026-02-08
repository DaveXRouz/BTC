"""V4 Oracle Service — Solver Layer.

All V3 solvers copied as-is. Oracle-type solvers (number, name, date)
run natively in the Python Oracle service. Scanner-type solvers
(unified_solver, scanner_solver, btc_solver) are kept as reference —
their logic moves to the Rust scanner in Phase 4.
"""

# Oracle-type solvers (run in Python)
from oracle_service.solvers.number_solver import NumberSolver
from oracle_service.solvers.name_solver import NameSolver
from oracle_service.solvers.date_solver import DateSolver

# Base class
from oracle_service.solvers.base_solver import BaseSolver
