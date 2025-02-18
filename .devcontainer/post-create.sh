# Install packages via poetry
cd /workspaces/ehubX
/opt/poetry/bin/poetry env use /usr/bin/python3.11
/opt/poetry/bin/poetry install
/opt/poetry/bin/poetry run sphinx-apidoc -o docs/source src/ehubx
rm docs/source/modules.rst
sed -i '/modules/c\   ehubx' docs/source/index.rst
/opt/poetry/bin/poetry run sphinx-build -M html docs/source docs/build
