# This is a simplified example demonstrating the functionality of all ehubX
# modules. It has a time horizon of length 3, two stages and a multitude of
# hubs. There are several demands on the ec E0 which are satisfied with a
# different module in each hub.
# In more detail:
#   - Hub H1 (conversion hub) Import E1 and convert it to E0 with XConv1
#   - Hub H2 (storage hub): Import E0 and use XStor2 to balance out a misfit
#                           between demand profile and import restrictions
#   - Hub H3 (solar hub): Import E2 (solar) convert it to E0 with XSolar3
#   - Hub H5 (load shedding hub): Import E0 to the max and shed the remaining
#                                 demand
#   - Hub H6 (load shifting hub): Import E0 and shift the load to balance out a
#                                 misfit between demand profile and import
#                                 restrictions
#   - Hub H7 (export hub): Import E0 and export it again to abide by the export
#                          restrictions
#   - Hub H8 & H9 (network hubs): Import E0 at H8 and export it again at H9 to
#                                 satisfy the demand profile
#   - H10 (multiobjective hub): There are two possibilities to satisfy the E0
#                               demand: Import it for free but with emissions,
#                               import E10 at a price but without emissions,
#                               then convert it to E0. The optimizer may choose
#                               whether to use the cost-minimal or CO2-minimal
#                               strategy (=> Multiobjective optimization)
#   - H11 (coupled tech hub): Import E11 and convert it to E0 via X11Conv but
#                             X11Conv is coupled to X11Main
#   - H12 (in_ec_group hub): Conversion tech X12Conv is defined on input ec
#                            group EG12 containing E12a and E12b. ehubX makes
#                            two techs out of this under the hood named
#                            X12Conv_E12a and X12Conv_E12b. Together they
#                            satisfy the demands
#   - H13 (heat pump): Import E13a, E13b and a heat pump to convert E13a -> E0
#                      and 13b -> E13c to satisfy E0 and E13c demands. Use
#                      E13d for power consumption
#   - H14 (ebm): Import E0 which is the ec of an EBM fleet with its own demand
#                and availability profiles.
import os

from pyomo.core import Constraint, Model, NonNegativeReals, Var

from ehubx import EhubX, FileGranularity, Gurobi, ObjectiveType


# Function for custom model modifications, used in step 4 of main method
def my_modifications(model: Model) -> None:
    # Add a variable
    model.V_MyVar = Var(domain=NonNegativeReals)

    # Add a constraint
    def _my_con(model):
        return model.V_MyVar == model.V_ImpCostTotal * 1.5

    model.C_MyCon = Constraint(rule=_my_con)


if __name__ == "__main__":
    # Step 0: Create EhubX object and set path
    ehubx = EhubX()
    # Set model path and parse
    ehubx.model_dir_path = os.path.abspath(os.path.dirname(__file__))
    ehubx.parse()
    # Step 2 (optional): Deactivate or reactivate modules
    ehubx.energy_system.deactivate_solar_techs()
    ehubx.energy_system.reactivate_solar_techs()
    # Step 3: Build the model. Use optional arguments to specify normalization
    #         and clustering
    ehubx.build()
    # Step 4 (optional): Add custom model modifications
    ehubx.modify_model(my_modifications)
    # Step 5 (optional): Manually set a solver and specify options
    solver = Gurobi()
    solver.set_mip_focus(1)
    solver.set_option_by_key("Method", 0)
    ehubx.set_solver(solver)
    # Step 6: Solve the model.
    ehubx.solve_single_obj(
        obj_type=ObjectiveType.COST, file_granularity=FileGranularity.MIN
    )
    ehubx.solve_double_obj(
        obj_type_1=ObjectiveType.COST,
        obj_type_2=ObjectiveType.CO2,
        num_pareto_points=10,
    )
    # Step 7 (optional): EhubX object can still be used to perform actions,
    #                    e.g.; modifying parameters and rebuilding the model
