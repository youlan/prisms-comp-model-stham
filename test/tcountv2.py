import matplotlib.pyplot as plt;
import pandas as pd;
import sqlite3;
import h5py;
import numpy as np;
from scipy.stats import linregress;
import pyproj
import matplotlib.lines as mlines
import sqlite3

datapath = "/uufs/chpc.utah.edu/common/home/u0403692/prog/prism/data/"
runpath = "/scratch/general/lustre/u0403692/"

gridsize = 100.0
stepsize=15
regmaxlat = 41.99773652
regminlat = 38.70051584
regminlong = -114.05593872
regmaxlong = -109.00222778

outproj = pyproj.Proj(init='epsg:4326');
inproj = pyproj.Proj(init='epsg:26912');

def latlongtrans(x):
	x.locx,x.locy=pyproj.transform(inproj,outproj,x.locx,x.locy);
	return x

def reversetrans(x):
	x.locx,x.locy=pyproj.transform(outproj,inproj,x.locx,x.locy);
	return x

def latlongtransraw(locx,locy):
	locx,locy=pyproj.transform(inproj,outproj,locx,locy);
	return locx,locy

def reversetransraw(locx,locy):
	locx,locy=pyproj.transform(outproj,inproj,locx,locy);
	return locx,locy

def getgrid(locx,locy, grid, mindims):
	x = int(np.floor(np.abs(locx-mindims[0]) / grid))
	y = int(np.floor(np.abs(locy-mindims[1]) / grid))
	return x,y

mindim = reversetransraw(regminlong,regminlat);
maxdim = reversetransraw(regmaxlong,regmaxlat);

#tag -333 is bad due to some anomalous effect
tags = [-627,-302,-619,-617,-616,-629,-332,-615,-301,-630,-408,-711,-354,-355,-407,-626,-501,-340,-353,-341]
# tags = [-627,-302,-617,-629,-615,-301,-630]
# tags = [-619, -332, -616,-408,-711,-354]
wdaydates = ["2014-04-02","2014-04-09","2014-04-16","2014-04-23","2014-04-30"]
wenddates = ["2014-04-06","2014-04-13","2014-04-20","2014-04-27","2014-05-04"]

tagmap = {b:ind for ind,b in enumerate(np.sort(tags))}
print(tagmap)
radarsite = pd.read_csv(datapath + "Automatic_Traffic_Recorder_Locations.csv")
tcounts = pd.read_excel(datapath + "2014ATRVolComb.xlsx")

coords = []
for i in tags:
	fr = radarsite[radarsite["ATR_NUMBER"]==i]
	coords += [ np.array([fr.LATITUDE.values,fr.LONGITUDE.values]).reshape(2) ]

coords = np.array(coords).reshape((len(tags),2)).T;
coords = pd.DataFrame({"atrnum":tags,"lat":coords[0],"long":coords[1]})
# coords[['locx','locy']] = coords[['long','lat']]
# coords[['locx','locy']] = coords[['locx','locy']].apply(reversetrans,axis=1)
# coords['x'] = coords['locx'].apply(lambda x: int(np.floor((x - mindim[0])/gridsize)))
# coords['y'] = coords['locy'].apply(lambda x: int(np.floor((x - mindim[1])/gridsize)))
# coords = pd.sort_values(coords["atrnum"])
print(coords);
# coords.to_csv(datapath + "atrvals.csv")


modcoords = pd.read_csv(datapath + "atrwaypoints.csv")
print(modcoords)
# exit()

# infile = h5py.File(runpath + "Ftraj4-2018-05-25_16-19-35-ForkPoolWorker-10.merge.sqlite3.h5",'r')




# plt.matshow(infile["/traj-slot-036-set-002"][:].T)
# plt.scatter(coords['x'].values,coords['y'].values,c='r',s=10)


simcounts = np.zeros((len(tags),24))
wdayrealcounts = np.zeros((len(tags),24));
wendrealcounts = np.zeros((len(tags),24));
regs = [];


longdelta = 0.00002
latdelta = 0.00002
con = sqlite3.connect(runpath + "Ftraj4-2018-09-13_15-54-07-ForkPoolWorker-10.merge.sqlite3")

# for ind,fr in coords.iterrows():
	# plt.scatter(fr.long,fr.lat,s=30,c='k')

# limiter = " limit 1000"
limiter = ""
for ind,fr in modcoords.iterrows():
	print(ind, fr.atr, end=" ",flush=True)
	data = pd.read_sql_query("select start from acttraj where lat between " +str(fr.lat - latdelta) + " and " +str(fr.lat + latdelta) + " and long between " +str(fr.long - longdelta) + " and " +str(fr.long + longdelta) + limiter, con)

	data["start"] = np.floor(data["start"] / 60.0)
	simcounts[tagmap[fr.atr]] += data['start'].value_counts(sort=False).reindex(np.arange(0,24),fill_value=0.0).values
	# plt.scatter(fr.long,fr.lat,s=30,c='r')
	# plt.scatter(data.long.values,data.lat.values,s=5,c='b');
	
	# plt.show()

con.close()
print(" ")
print(simcounts);
print(np.sum(simcounts,axis=0))
print(np.sum(simcounts,axis=1))
# plt.show()
# exit()

print("realcounts")
def count24(x,y,infile):
	# print(x,y)
	vals = np.zeros(96);
	for i in range(0,96):
		vals[i] = infile["/traj-slot-"+str(i).zfill(3)+"-set-002"][x][y]
	vals = vals.reshape((24,4))
	vals = np.sum(vals,axis=1)
	return vals

def getrealcts(atrnum,date,tcounts):
	
	fr = tcounts[tcounts["Date"]==str(date)][tcounts["ATR"]==atrnum];
	# print(fr)
	if(len(fr) < 1):
		print("Bad date/atr pairing")
		print(atrnum,date)
		return None
	p = fr.iloc[0].iloc[2:26].values
	return np.roll(p,-4)

radlimit = 1
for ind,fr in coords.iterrows():
	
	# for i in np.arange(-radlimit,radlimit + 1):
	# 	for j in np.arange(-radlimit,radlimit + 1):
	# 		simcounts[ind] += count24(int(fr.x+i),int(fr.y+j),infile)
	# simcounts[ind] += count24(int(fr.x),int(fr.y),infile)
	c = 0;
	for d in wdaydates:	
		p = getrealcts(fr.atrnum,d,tcounts)
		if p is None:
			continue;
		wdayrealcounts[tagmap[fr.atrnum]] += p.astype("float64")
		c += 1
	if (c != 0):
		wdayrealcounts[tagmap[fr.atrnum]] /= c;

	c = 0
	for d in wenddates:	
		p = getrealcts(fr.atrnum,d,tcounts)
		if p is None:
			continue;
		wendrealcounts[tagmap[fr.atrnum]] += p.astype("float64")
		c += 1
	if (c != 0):
		wendrealcounts[tagmap[fr.atrnum]] /= c;

# simcounts /= 9.0

# print(wdaycounts);
# print(np.sum(wdaycounts,axis=0))
# print(np.sum(wdaycounts,axis=1))


outfile = h5py.File(datapath + "trafficcounts.h5",'w')
ds = outfile.create_dataset("/simcounts", data=simcounts,fillvalue=0.,compression='gzip',compression_opts=9)
ds = outfile.create_dataset("/wdayrealcounts", data=wdayrealcounts,fillvalue=0.,compression='gzip',compression_opts=9)
ds = outfile.create_dataset("/wendrealcounts", data=wendrealcounts,fillvalue=0.,compression='gzip',compression_opts=9)
ds = outfile.create_dataset("/atrlabels", data=np.array(list(tagmap)),compression='gzip',compression_opts=9)
outfile.close();


# for ind,fr in coords.iterrows():
# 	plt.scatter(simcounts[ind],realcounts[ind],label=str(fr.atrnum),s=10)
# 	# plart = plt.plot(,label=str(fr.atrnum),)
# 	# col = plart[0].get_color();
# 	# plt.plot(,c=col,linestyle=':')
	
reg = linregress(simcounts.flatten(),wendrealcounts.flatten())
print("Weekend:",reg, reg.rvalue**2)
reg = linregress(simcounts.flatten(),wdayrealcounts.flatten())
print("Weekday:",reg, reg.rvalue**2)
# plt.legend()
# plt.show()




print("plotting")

fig = plt.figure(figsize=(4.0,3.0))
ax = fig.add_subplot(111)

# simcounts /= np.max(simcounts)
# wdayrealcounts /= np.max(wdayrealcounts)
# wendrealcounts /= np.max(wendrealcounts)

for ind,fr in coords.iterrows():
	plart = ax.plot(simcounts[ind]/np.max(simcounts[ind]),label=str(fr.atrnum),color='k',linewidth=0.95,alpha=0.75)
	col = plart[0].get_color();
	ax.plot(wendrealcounts[ind]/np.max(wendrealcounts[ind]),c=col,linestyle=':',color='r',linewidth=0.95,alpha=0.75)
	ax.plot(wdayrealcounts[ind]/np.max(wdayrealcounts[ind]),c=col,linestyle='--',color='b',linewidth=0.95,alpha=0.75)
	# plart = ax.plot(simcounts[ind],label=str(fr.atrnum),color='k',linewidth=0.95,alpha=0.75)
	# col = plart[0].get_color();
	# ax.plot(wendrealcounts[ind],c=col,linestyle=':',color='r',linewidth=0.95,alpha=0.75)
	# ax.plot(wdayrealcounts[ind],c=col,linestyle='--',color='b',linewidth=0.95,alpha=0.75)
# plt.legend()
plart = mlines.Line2D([], [], color='k',linewidth=0.95, alpha=0.75)
rplart = mlines.Line2D([], [], color='r',linestyle=':',linewidth=0.95, alpha=0.75)
bplart = mlines.Line2D([], [], color='b',linestyle='--',linewidth=0.95, alpha=0.75)
fontsize = 12
# ax.set_xlim(-1,97)
ax.set_xticks([0,6,12,18,24])
ax.set_xticklabels(['4:00','10:00','16:00','22:00','4:00'],fontsize=fontsize)
ax.set_xlabel("Time",fontsize=fontsize)

legart = [plart,bplart,rplart]
leglabels = [ "Sim", "Wday", "Wend" ]
ax.legend(handles=legart,labels=leglabels)
plt.tight_layout()
# plt.show()
plt.savefig('trafficcompare.eps',dpi = 300)


