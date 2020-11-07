import streamlit as st, pandas as pd, numpy as np, plotly.graph_objects as go
from dateutil.relativedelta import relativedelta

#below set the page to wide format, much easier to view things
st.beta_set_page_config(layout="wide")
st.image('Logo.png',width=500)
#this caches the data so each interaction doesnt require reloading the data set
@st.cache
def load_data():
    df = pd.read_csv('MB_latest_prd Producing Entity Monthly Production.csv')
    return df
@st.cache(allow_output_mutation=True)
def load_data2():
	df_params=pd.read_csv('MB_DCA_parameters_per_Well.csv')
	return df_params
@st.cache(allow_output_mutation=True)
def load_data3():
	df_headers=pd.read_csv('MB_latest_prd Production Headers.csv')
	return df_headers
@st.cache(allow_output_mutation=True)
def load_data4():
	df_elio_base=pd.read_excel('MB_Elio.xlsx',sheet_name='BaseCase')
	df_elio_base['Monthly']=df_elio_base['Exp Rate']*30.44
	return df_elio_base
@st.cache(allow_output_mutation=True)
def load_data5():
	df_heatmap=pd.read_csv('MB Well Headers.csv')
	return df_heatmap
@st.cache(allow_output_mutation=True)
def load_data6():
	dfall=pd.read_csv('dfall.CSV')
	return dfall

#This is Arps equation turned into a function
def dca(t,qi,b,d):
    if b==0:
        return qi*np.exp(-1*d*t) #exponential
    elif b==1:
        return qi/(1+d*t) #harmonic
    elif b>=1:
        return 0 #limiting b to values equal to or less than 1
    else:
        return qi*((1+b*d*t)**(-1/b)) #exponential    

#load in the data cache
df = load_data() 
df_params=load_data2()
df_headers=load_data3()
df_elio_base=load_data4()
df_heatmap_wells=load_data5()
dfall=load_data6()

df_elio_base_sub=df_elio_base[df_elio_base['Date']>'8/1/2020']
df_elio_base_sub=df_elio_base_sub.groupby(df_elio_base_sub.Date.dt.year).sum().cumsum()
# df_elio_base_sub=df_elio_base_sub[df_elio_base_sub.index<2035]


#The main program is within here
def main(): 
	page = st.sidebar.selectbox("Choose a page", ["Full Field", "Individual Wells","Field Map","Well Spacing"])
	if page == "Full Field":
		#give a title to the page that is the well name
		st.header('Monument Butte Full Field Production')
		df = pd.read_csv('MB_latest_prd Producing Entity Monthly Production.csv')
		#subset the data to only use singel well data
		df_sub=df.groupby('Monthly Production Date').sum().reset_index()
		df_sub['Monthly Production Date']=pd.to_datetime(df_sub['Monthly Production Date'])
		df_sub=df_sub[df_sub['Monthly Production Date']>'1/1/2000']
		
		#set three columns for high -low-mid cases
		cols = st.beta_columns(3)
		
		#first column is the P50 case
		cols[0].write("Mid Case (P50)")
		Di50 = float(cols[0].text_input("Decline Rate, 1/year", 0.14))
		Qi50 = cols[0].text_input('Initial Rate, bbl/month',165000)
		Qi50 = float(Qi50)
		b50 = cols[0].text_input('b-factor',0.4)
		b50 = float(b50)
		
		#second column is the P90 case
		cols[1].write("Low Case (P90)")
		Di90 = float(cols[1].text_input("P90 Decline Rate, 1/year", 0.185))
		Qi90 = cols[1].text_input('P90 Initial Rate, bbl/month',150000)
		Qi90 = float(Qi90)
		b90 = cols[1].text_input('P90 b-factor',0)
		b90 = float(b90)
		
		#third column is the P10 case
		cols[2].write("High Case (P10)")
		Di10 = float(cols[2].text_input("P10 Decline Rate, 1/year", 0.11))
		Qi10 = cols[2].text_input('P10 Initial Rate, bbl/month',180000)
		Qi10 = float(Qi10)
		b10 = cols[2].text_input('P10 b-factor',0.8)
		b10 = float(b10)
		
		df_dca=pd.DataFrame({'Months':list(range(-66,368))})
		df_dca['Qcalc_50']=dca(df_dca['Months'],Qi50,b50,Di50/12)
		df_dca['Qcalc_90']=dca(df_dca['Months'],Qi90,b90,Di90/12)
		df_dca['Qcalc_10']=dca(df_dca['Months'],Qi10,b10,Di10/12)
		
		dates=[]
		for month in df_dca.Months:
			dates.append(pd.to_datetime(df_sub['Monthly Production Date'][-1:].values[0])+relativedelta(months=+month))
		df_dca['Date']=dates

		# df_sub=df_sub[df_sub['Monthly Production Date']>pd.to_datetime('1/1/2016')]
		cols=st.beta_columns(2)
		if cols[0].button('Zoom In'):
			df_sub=df_sub[df_sub['Monthly Production Date']>pd.to_datetime('1/1/2016')]
		else:
			pass
		if cols[1].button('Zoom Out'):
			df_sub=df.groupby('Monthly Production Date').sum().reset_index()
			df_sub['Monthly Production Date']=pd.to_datetime(df_sub['Monthly Production Date'])
		else:
			pass
		df_dca_yr=df_dca.groupby(df_dca.Date.dt.year).sum()
		df_sub_yr=df_sub.groupby(df_sub['Monthly Production Date'].dt.year).sum()
		
		fig=go.Figure()
		fig.add_trace(go.Scatter(marker_color='green',name='History',mode='markers',x=df_sub['Monthly Production Date'],y=df_sub['Monthly Oil']/30.44))
		fig.add_trace(go.Scatter(name='P50',x=df_dca['Date'],y=df_dca['Qcalc_50']/30.44))
		fig.add_trace(go.Scatter(name='P90',x=df_dca['Date'],y=df_dca['Qcalc_90']/30.44))
		fig.add_trace(go.Scatter(name='P10',x=df_dca['Date'],y=df_dca['Qcalc_10']/30.44))
		# fig.add_trace(go.Scatter(name='Historic Yearly Average',x=df_sub_yr.index,y=df_sub_yr['Monthly Oil'][:-1]/12/30.44))
		fig.add_trace(go.Scatter(line=dict(color='black',dash='dash'),name='Elio\'s',x=df_elio_base['Date'],y=df_elio_base['Exp Rate']))
		fig.update_yaxes(type="log",range=[0,5])
		fig.update_layout(title='Semi-Log Scale',yaxis_title='Daily Oil, bbl')
		
		fig2=go.Figure()
		fig2.add_trace(go.Scatter(marker_color='green',name='History',mode='markers',x=df_sub['Monthly Production Date'],y=df_sub['Monthly Oil']/30.44))
		fig2.add_trace(go.Scatter(name='P50',x=df_dca['Date'],y=df_dca['Qcalc_50']/30.44))
		fig2.add_trace(go.Scatter(name='P90',x=df_dca['Date'],y=df_dca['Qcalc_90']/30.44))
		fig2.add_trace(go.Scatter(name='P10',x=df_dca['Date'],y=df_dca['Qcalc_10']/30.44))
		# fig2.add_trace(go.Scatter(name='Historic Yearly Average',x=df_sub_yr.index,y=df_sub_yr['Monthly Oil'][:-1]/12/30.44))
		fig2.add_trace(go.Scatter(line=dict(color='black',dash='dash'),name='Elio\'s',x=df_elio_base['Date'],y=df_elio_base['Exp Rate']))
		fig2.update_layout(title='Normal Scale')
		fig2.update_yaxes(title='Daily Oil, bopd',type="-",range=None)
		
		cols[0].plotly_chart(fig)
		cols[1].plotly_chart(fig2)
		
		df_dca_cum=df_dca[df_dca.Date>'8/1/2020']
		df_dca_cum=df_dca_cum.groupby(df_dca_cum.Date.dt.year).sum()
		df_dca_cum['50_cum'],df_dca_cum['90_cum'],df_dca_cum['10_cum']=df_dca_cum['Qcalc_50'].cumsum(),df_dca_cum['Qcalc_90'].cumsum(),df_dca_cum['Qcalc_10'].cumsum()

		df_summary=pd.DataFrame({'Year':df_dca_cum.index,'P50':df_dca_cum['Qcalc_50'].to_list(),'P90':df_dca_cum['Qcalc_90'].to_list(),'P10':df_dca_cum['Qcalc_10'].to_list()})
		df_summary['P50'],df_summary['P90'],df_summary['P10']=df_summary['P50']/1000,df_summary['P90']/1000,df_summary['P10']/1000
		# df_summary['Elio\'s']=df_elio_base_sub.Monthly.to_list()
		# df_summary['Elio\'s']=df_summary['Elio\'s']/1000

		fig3=go.Figure()
		fig3.add_trace(go.Scatter(name='P50',x=df_dca_cum.index,y=df_dca_cum['50_cum']))
		fig3.add_trace(go.Scatter(name='P90',x=df_dca_cum.index,y=df_dca_cum['90_cum']))
		fig3.add_trace(go.Scatter(name='P10',x=df_dca_cum.index,y=df_dca_cum['10_cum']))
		fig3.add_trace(go.Scatter(mode='lines',line=dict(color='black', dash='dash'),name='Elio\'s',x=df_elio_base_sub.index,y=df_elio_base_sub.Monthly))
		fig3.update_layout(title='Cumulatives',yaxis_title='Cum. Oil, bbl')

		cols[0].plotly_chart(fig3)

		if cols[1].button('Export data to Monument Butte Folder in Operations Drive'):
			df_summary.to_csv('MB_DCA.csv')
		else:
			pass

		cols[1].write('Cumulative Sums, Mbbl')
		cols[1].write(pd.concat([df_summary.Year,df_summary.cumsum().drop(columns=['Year'])],axis=1))

		pv=float(cols[0].text_input('Discount Rate, %',10))
		df_elio_sub_sub=df_elio_base[df_elio_base['Date']>'8/1/2020']
		df_elio_sub_sub=df_elio_sub_sub.groupby(df_elio_sub_sub.Date.dt.year).sum()
		df_elio_sub_sub['Discount Months']=range(4,365,12)
		df_elio_sub_sub['Discount Rate']=1/(1+(pv/100/12))**df_elio_sub_sub['Discount Months']
		df_elio_sub_sub['Discounted BBLs Rate']=df_elio_sub_sub['Discount Rate']*df_elio_sub_sub['Monthly']
		df_summary['Discount Months']=range(4,377,12)
		df_summary['Discount Rate']=1/(1+(pv/100/12))**df_summary['Discount Months']
		df_summary['P50 Disc BBLs Rate'],df_summary['P90 Disc BBLs Rate'],df_summary['P10 Disc BBLs Rate']=df_summary['Discount Rate']*df_summary['P50'],df_summary['Discount Rate']*df_summary['P90'],df_summary['Discount Rate']*df_summary['P10']
		disc_sums=[]
		for xxx in ['P50 Disc BBLs Rate','P90 Disc BBLs Rate','P10 Disc BBLs Rate']:
			disc_sums.append(df_summary[xxx].sum())
		disc_sums.append(df_elio_sub_sub['Discounted BBLs Rate'].sum()/1000)
		cases=['P50','P90','P10','Elio\'s']
		df_disc=pd.DataFrame({'Case':cases,'Disc. BBLs':disc_sums})
		df_disc=df_disc.sort_values('Disc. BBLs')
		fig4 = go.Figure([go.Bar(x=df_disc.Case, y=df_disc['Disc. BBLs'])])
		fig4.update_layout(title_text='Cumulative Discounted BBLs per Case')
		cols[0].plotly_chart(fig4)
		cols[1].text('  .\n\n\n\n\n\n\n\n\n Cum. Discounted Barrels Table')
		cols[1].table(df_disc)
		
		# cols=st.beta_columns(3)
		# cols[0].text_input('Oil price, $/bbl',30)
		# cols[1].text_input('Gas price, $/Mcf',0)
		# cols[2].text_input('Ad Valorem + Severence, %',12)
		# cols[0].text_input('Fixed OPEX, $',4800000)
		# cols[1].text_input('Variable OPEX, $/bbl',15.37)
		# cols[2].text_input('Purchase Price, $MM',30)
		# cols[0].text_input('Discount Rate, %',10)
		# cols[1].text_input('NRI, %',80)

	if page == "Individual Wells":
		df = pd.read_csv('C:/Users/Elii/Desktop/Working/X Oil/Monument Butte/app/MB_latest_prd Producing Entity Monthly Production.csv')
		#Create a sidebar that allows for cycling through each well
		well = st.selectbox("Choose a well", df['API/UWI'].unique())
		#give a title to the page that is the well name
		st.header(well)
		
		#subset the data to only use singel well data
		df_sub=df[df['API/UWI']==well]
		
		#set three columns for high -low-mid cases
		cols = st.beta_columns(3)
		
		#first column is the P50 case
		cols[0].write("Mid Case (P50)")
		Di50 = float(cols[0].text_input("Decline Rate, 1/year", float(df_params[df_params['Well']==well]['Di_50'])))
		Qi50 = cols[0].text_input('Initial Rate, bbl/month',float(df_params[df_params['Well']==well]['Qi_50']))
		Qi50 = float(Qi50)
		b50 = cols[0].text_input('b-factor',float(df_params[df_params['Well']==well]['b_50']))
		b50 = float(b50)
		df_params.loc[df_params.index[df_params['Well']==well],'Qi_50']=Qi50
		df_params.loc[df_params.index[df_params['Well']==well],'b_50']=b50
		df_params.loc[df_params.index[df_params['Well']==well],'Di_50']=Di50
		
		#second column is the P90 case
		cols[1].write("Low Case (P90)")
		Di90 = float(cols[1].text_input("P90 Decline Rate, 1/year", float(df_params[df_params['Well']==well]['Di_90'])))
		Qi90 = cols[1].text_input('P90 Initial Rate, bbl/month',float(df_params[df_params['Well']==well]['Qi_90']))
		Qi90 = float(Qi90)
		b90 = cols[1].text_input('P90 b-factor',float(df_params[df_params['Well']==well]['b_90']))
		b90 = float(b90)
		df_params.loc[df_params.index[df_params['Well']==well],'Qi_90']=Qi90
		df_params.loc[df_params.index[df_params['Well']==well],'b_90']=b90
		df_params.loc[df_params.index[df_params['Well']==well],'Di_90']=Di90
		
		#third column is the P10 case
		cols[2].write("High Case (P10)")
		Di10 = float(cols[2].text_input("P10 Decline Rate, 1/year", float(df_params[df_params['Well']==well]['Di_10'])))
		Qi10 = cols[2].text_input('P10 Initial Rate, bbl/month',float(df_params[df_params['Well']==well]['Qi_10']))
		Qi10 = float(Qi10)
		b10 = cols[2].text_input('P10 b-factor',float(df_params[df_params['Well']==well]['b_10']))
		b10 = float(b10)
		df_params.loc[df_params.index[df_params['Well']==well],'Qi_10']=Qi10
		df_params.loc[df_params.index[df_params['Well']==well],'b_10']=b10
		df_params.loc[df_params.index[df_params['Well']==well],'Di_10']=Di10
		
		df_dca=pd.DataFrame({'Months':list(range(-24,173))})
		df_dca['Qcalc_50']=dca(df_dca['Months'],Qi50,b50,Di50/12)
		df_dca['Qcalc_90']=dca(df_dca['Months'],Qi90,b90,Di90/12)
		df_dca['Qcalc_10']=dca(df_dca['Months'],Qi10,b10,Di10/12)
		
		dates=[]
		for month in df_dca.Months:
			dates.append(pd.to_datetime(df_sub['Monthly Production Date'][-1:].values[0])+relativedelta(months=+month))
		df_dca['Date']=dates
		df_dca['API']=well

		#st.write('Total Future PDP: %.0f' %(df_dca['Qcalc_50'][1:].sum()))

		fig=go.Figure()
		fig.add_trace(go.Scatter(marker_color='green',name='History',mode='markers',x=df_sub['Monthly Production Date'],y=df_sub['Monthly Oil']))
		fig.add_trace(go.Scatter(name='P50',x=df_dca['Date'],y=df_dca['Qcalc_50']))
		fig.add_trace(go.Scatter(name='P90',x=df_dca['Date'],y=df_dca['Qcalc_90']))
		fig.add_trace(go.Scatter(name='P10',x=df_dca['Date'],y=df_dca['Qcalc_10']))
		fig.update_yaxes(type="log")
		
		fig2=go.Figure()
		fig2.add_trace(go.Scatter(marker_color='green',name='History',mode='markers',x=df_sub['Monthly Production Date'],y=df_sub['Monthly Oil']))
		fig2.add_trace(go.Scatter(name='P50',x=df_dca['Date'],y=df_dca['Qcalc_50']))
		fig2.add_trace(go.Scatter(name='P90',x=df_dca['Date'],y=df_dca['Qcalc_90']))
		fig2.add_trace(go.Scatter(name='P10',x=df_dca['Date'],y=df_dca['Qcalc_10']))
		
		cols[0].plotly_chart(fig)
		cols[1].plotly_chart(fig2)
		# cols[0].write(df_params)
		
		if st.button('Save Decline Parameters'):
			df_params.to_csv('MB_DCA_parameters_per_Well.csv')
		else:
			pass

		#Map Below
		df_headers2=df_headers

		df_headers2['Class_Color']=df_headers['Production Type'].map({'WTR INJ':'cyan','OIL':'green','GAS':'red','DRY':'black','WTR SRC':'blue','Test Well':'black'})
		fig = go.Figure(go.Scattermapbox(
			fill = 'none',
			lon = df_headers2['Surface Longitude (WGS84)'], lat = df_headers2['Surface Latitude (WGS84)'],
			marker = { 'size': 6 ,'color':df_headers2['Class_Color']},
		hovertext=df_headers2['API/UWI']))
		fig.add_trace(go.Scattermapbox(
			fill = 'none',
			lon = df_headers2['Surface Longitude (WGS84)'][df_headers2['API/UWI']==well], lat = df_headers2['Surface Latitude (WGS84)'][df_headers2['API/UWI']==well],
			marker = {'size': 25 ,'color':'magenta'},
			hovertext=df_headers2['API/UWI'][df_headers2['API/UWI']==well]))

		fig.update_layout(
			mapbox = {
				'style': "stamen-toner",
				'center': {'lon': df_headers2['Surface Longitude (WGS84)'].mean(), 'lat': df_headers2['Surface Latitude (WGS84)'].mean() },
				'zoom': 11},
			showlegend = False)

		fig.update_layout(width=1500,height=800,
			mapbox_style="white-bg",
			mapbox_layers=[
				{
					"below": 'traces',
					"sourcetype": "raster",
					"sourceattribution": "United States Geological Survey",
					"source": [
						"https://basemap.nationalmap.gov/arcgis/rest/services/USGSImageryOnly/MapServer/tile/{z}/{y}/{x}"
					]
				}
			])
		st.plotly_chart(fig)

	if page == "Field Map":
		df_headers2=df_headers
		if st.button('Only Show ACTIVE wells'):
			df_headers2=df_headers[df_headers['Producing Status']=='ACTIVE']
		else:
			df_headers2=df_headers

			
		df_headers2['Class_Color']=df_headers['Production Type'].map({'WTR INJ':'cyan','OIL':'green','GAS':'red','DRY':'black','WTR SRC':'blue','Test Well':'black'})
		fig = go.Figure(go.Scattermapbox(
			fill = 'none',
			lon = df_headers2['Surface Longitude (WGS84)'], lat = df_headers2['Surface Latitude (WGS84)'],
			marker = { 'size': 10 ,'color':df_headers2['Class_Color']},
		hovertext=df_headers2['API/UWI']))

		fig.update_layout(
			mapbox = {
				'style': "stamen-toner",
				'center': {'lon': df_headers2['Surface Longitude (WGS84)'].mean(), 'lat': df_headers2['Surface Latitude (WGS84)'].mean() },
				'zoom': 11},
			showlegend = False)

		fig.update_layout(width=1500,height=800,
			mapbox_style="white-bg",
			mapbox_layers=[
				{
					"below": 'traces',
					"sourcetype": "raster",
					"sourceattribution": "United States Geological Survey",
					"source": [
						"https://basemap.nationalmap.gov/arcgis/rest/services/USGSImageryOnly/MapServer/tile/{z}/{y}/{x}"
					]
				}
			])
		st.plotly_chart(fig)
	if page== "Well Spacing":
		st.header('Well Spacing Bubble Map')
		st.write('\*Tooltip shows the calculated spacing in acres\*')
		st.write('\*Bubble sized by acres ')
		# df_heatmap=pd.read_csv('MB Well Headers.csv')
		dfall=pd.read_csv('dfall.CSV')
		df=df_heatmap_wells
		dfall=dfall.sort_values('Dist.', ascending=False)
		df=df[(df['Well Status']!='P & A')& (df['Well Status']!='CANCELLED')]
		dft=df[['API14','Surface Hole Latitude (WGS84)','Surface Hole Longitude (WGS84)']].set_index('API14')
		dfallt=dfall.set_index('Well')
		temp=dft.join(dfallt)
		temp=temp.sort_values('Dist.',ascending=False)[7:]

		fig = go.Figure(go.Scattermapbox(
				lat=temp['Surface Hole Latitude (WGS84)'],
				lon=temp['Surface Hole Longitude (WGS84)'],
				mode='markers',
				marker=go.scattermapbox.Marker(
					size=temp['Spacing']*2,
					color=temp['Spacing'],
					colorscale='Portland',
				),
				text=temp['Spacing']
			))
		fig.update_layout(width=1500,height=800,mapbox_style="white-bg",mapbox_layers=[{"below": 'traces',"sourcetype": "raster",
							"sourceattribution": "United States Geological Survey","source": [
								"https://basemap.nationalmap.gov/arcgis/rest/services/USGSImageryOnly/MapServer/tile/{z}/{y}/{x}"]}])
		fig.update_layout(
			mapbox = {
				'center': {'lon': temp['Surface Hole Longitude (WGS84)'].mean(), 'lat': temp['Surface Hole Latitude (WGS84)'].mean() },
				'zoom': 11},
			showlegend = False)
		st.plotly_chart(fig)



if __name__ == "__main__":
    main()
