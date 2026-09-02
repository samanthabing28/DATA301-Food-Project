Low Food Access by State Map, Reproducibility

This map will not be reproducible by anyone without an ArcGIS pro license (of which I have through the University). This is because it pulls a State Boundary geometry via the R-ArcGIS Bridge through arcgisbinding. 

To reproduce this:
- R 4.4+
- ArcGIS Pro with R-ArcGIS bridge configured
- packages: arcgisbinding, dplyr, classInt, ggplot2, ggrepel, sf
- food_access_clean_2019_M.csv 
- Local export of the Living Atlas "USA States Generalized" layer

The output will be: low_access_by_state_map.pdf 
The output will be located in the same directory as the map.rmd file. 

For the group report, the PDF has been supplied directily rather than reproduced by other members due to the ArcGIS dependency not being viable for the whole group. 
