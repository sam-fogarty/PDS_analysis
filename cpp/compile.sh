g++ -c daphne.cpp -o daphne.o
ar rcs libdaphne.a daphne.o
g++ plot_data.cpp daphne.cpp -o plot_data -I$ROOTSYS/include -L$ROOTSYS/lib -lCore -lRIO -lNet -lHist -lGraf -lGraf3d -lGpad -lTree -lRint -lPostscript -lMatrix -lPhysics -lMathCore -lThread -lGui -L. -ldaphne
g++ collect_data.cpp daphne.cpp -o collect_data -I$ROOTSYS/include -L$ROOTSYS/lib -lCore -lRIO -lNet -lHist -lGraf -lGraf3d -lGpad -lTree -lRint -lPostscript -lMatrix -lPhysics -lMathCore -lThread -lGui -L. -ldaphne
