# This script has to be run as su and copies your license file from
# .devcontainer/gurobi.lic and copies it to the correct system locations
cp /workspaces/ehubX/.devcontainer/gurobi.lic /opt/gurobi/gurobi1101/gurobi.lic
cp /workspaces/ehubX/.devcontainer/gurobi.lic /home/vscode/gurobi.lic
