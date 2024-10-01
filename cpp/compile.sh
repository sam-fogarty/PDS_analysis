g++ -c daphne.cpp -o daphne.o
ar rcs libdaphne.a daphne.o
#g++ plot_data.cpp daphne.cpp -o plot_data -I$ROOTSYS/include -L$ROOTSYS/lib -lCore -lRIO -lNet -lHist -lGraf -lGraf3d -lGpad -lTree -lRint -lPostscript -lMatrix -lPhysics -lMathCore -lThread -lGui -L. -ldaphnei
g++ collect_data.cpp daphne.cpp -o collect_data -L/root/PDS_scripts/cpp -ldaphne -I/root/PDS_scripts/cpp/hdf5-1.14.4-3/hdf5/include -L/root/PDS_scripts/cpp/hdf5-1.14.4-3/hdf5/lib -lhdf5 -lhdf5_cpp -I/root/miniconda3/lib -L/root/miniconda3/lib -lz -Wl,-rpath,/root/miniconda3/lib -Wl,-rpath,/root/PDS_scripts/cpp/hdf5-1.14.4-3/hdf5/include/H5Cpp.h  #-I$ROOTSYS/include -L$ROOTSYS/lib -lCore -lRIO -lNet -lHist -lGraf -lGraf3d -lGpad -lTree -lRint -lPostscript -lMatrix -lPhysics -lMathCore -lThread -lGui -L. -ldaphne
