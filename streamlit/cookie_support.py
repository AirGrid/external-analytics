import numpy as np
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from scipy import stats

#################
# Data          #
#################

DATA_URL = 'https://storage.googleapis.com/ag-external-data/airgrid_blog_network_cookie_support.csv'

st.set_page_config(
    page_title='AirGrid - 3P Cookie Support Analysis',
    page_icon='https://app.airgrid.io/images/favicon-32x32.png')

@st.cache(persist=True)
def load_data(nrows):
    df = pd.read_csv(DATA_URL, nrows=nrows)
    df['date'] = pd.to_datetime(df.date, format='%Y-%m-%d')
    return df

df = load_data(nrows=None)

top_devices = ['desktop', 'mobile', 'tablet']
top_browsers = df.groupby('browser_name').sum().reset_index().sort_values(by='traffic', ascending=False).head(14).browser_name.to_list()

by_day = df.groupby('date').sum().reset_index()
by_day['cookie_support_pct'] = (by_day.cookies_supported / by_day.traffic) * 100

by_device = df[df.device_type.isin(['desktop', 'mobile', 'tablet'])]
by_device = pd.pivot_table(by_device, values='traffic', index=['date'], columns=['device_type'], aggfunc=np.sum)
by_device['total'] = by_device.sum(axis=1)
by_device['mobile_tablet'] = by_device.mobile + by_device.tablet 
by_device['mobile_tablet_pct'] = (by_device.mobile_tablet / by_device.total) * 100

total_by_device = df[df.device_type.isin(top_devices)]
total_by_device = total_by_device.groupby('device_type').sum().reset_index()
total_by_device['cookie_support_pct'] = (total_by_device.cookies_supported / total_by_device.traffic) * 100

by_browser = pd.pivot_table(df, values='traffic', index=['date'], columns=['browser_name'], aggfunc=np.sum)
by_browser['total'] = by_browser.sum(axis=1)
by_browser['chrome_pct'] = (by_browser.Chrome / by_browser.total) * 100

filtered_df = df[df.device_type.isin(
    top_devices) & df.browser_name.isin(top_browsers)]

def filter_df_by_options(df, device_type=None, browser_name=None):
    if device_type:
        df = df[df.device_type==device_type]
    if browser_name:
        df = df[df.browser_name==browser_name]
    return df

#################
# Plotting      #
#################

def line_of_best_fit(dates, y):
    x = [i.toordinal() for i in dates]
    slope, intercept, _, _, _ = stats.linregress(x, y)
    def g(x):
        return slope * x + intercept
    vals = list(map(g, x))
    return vals

def plot_stat_by_date(dates, primary_stat, best_fit=None, y_label='Cookie Support %'):
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(dates, primary_stat, color='#2C5EF6')
    if best_fit:
        ax.plot(dates, best_fit, color='#FFAE73')

    # Format X Axis
    months = mdates.MonthLocator()
    monthsFmt = mdates.DateFormatter('%b-%Y')
    ax.xaxis.set_major_locator(months)
    ax.xaxis.set_major_formatter(monthsFmt)
    ax.tick_params(axis='x', labelsize=8)

    # Format Y Axis
    ax.set_ylim([0,100])
    ax.tick_params(axis='y', labelsize=8)
    ax.set_ylabel(y_label, fontsize=10)

    # Remove spines
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)
    return (fig, ax)

def total_support_by_device(labels, cookie_support_pct):
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(labels, cookie_support_pct, color=['#2C5EF6', '#BD69FF', '#394873'])
    # Format Y Axis
    ax.set_ylim([0,100])
    ax.tick_params(axis='y', labelsize=8)
    ax.set_ylabel('Cookie Support %', fontsize=10)
    # Remove spines
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)
    return (fig, ax)


#################
# App           #
#################

st.title('AirGrid 3P Cookie Support Analysis')

st.markdown(
    """
    This analysis is a follow up to the [article](https://medium.com/@ag_internal/cookie-support-analysis-in-the-airgrid-blog-network)
    posted on the [AirGrid](https://airgrid.io) blog.
    """
)

st.header('Cookie support over time')

st.markdown(
    """
    Google recently made the [announcement](https://www.theverge.com/2021/6/24/22547339/google-chrome-cookiepocalypse-delayed-2023) 
    that 3rd party cookies are going to hang around for a little while longer (~2 years),
    which prompted the question **"How many cookies are there today?"**
    """
)

best_fit_cookie_support = line_of_best_fit(by_day.date.to_list(), by_day.cookie_support_pct.to_list())
st.pyplot(plot_stat_by_date(by_day.date, by_day.cookie_support_pct, best_fit_cookie_support)[0])

st.markdown(
    """
    The percentage of site traffic which accepts cookies has hit around **29%** 🤯, but the more important pattern is that
    this number is on the decline. Even with the Google delay, the number of cookies available for online
    advertising and user tracking will be **0** before we hit the official "cookiepocalypse".
    """
)

st.header('Growth in mobile')

st.markdown(
    """
    The primary reason for the organic decline of cookie supporting traffic is that mobile traffic is on the rise. The dominance
    of Chrome is less prevelant on mobile, but also Chrome on iOS is actually just Safari with a Chrome logo, due to the
    [App Store Review Guidelines](https://developer.apple.com/app-store/review/guidelines/#software-requirements):

    > 2.5.6 Apps that browse the web must use the appropriate WebKit framework and WebKit Javascript.

    *For the curious: the spikes we see in mobile traffic are the weekends! People have thrown the work laptop in the cupboard and
    browse the web using their mobiles.*
    """
)

best_fit_mobile = line_of_best_fit(by_device.index.to_list(), by_device.mobile_tablet_pct.to_list())
st.pyplot(
    plot_stat_by_date(
        by_device.index, 
        by_device.mobile_tablet_pct,
        best_fit_mobile,
        'Mobile Traffic %')[0])

st.markdown(
    """
    We can confirm our suspicions by looking at the average % of cookie support across each device type.
    """
)

st.pyplot(total_support_by_device(total_by_device.device_type, total_by_device.cookie_support_pct)[0])

st.markdown(
    """
    While mobile traffic continues to grow, we expect a natural decline in the traffic that accepts 3P cookies.
    """
)

st.header('Slice and dice')

st.markdown(
    """
    For those of you who have followed this far, a special treat exists! Below you are able to select a device type & browser combination 
    to view the % of cookie supporting traffic.
    """
)

device_option = st.selectbox(
    'Select an optional device type filter:',
    [None] + top_devices)

browser_option = st.selectbox(
    'Select an optional browser filter:',
    [None] + top_browsers)

st.write('You selected a device filter:', device_option, 'and browser filter:', browser_option)

slice_dice_df = filter_df_by_options(filtered_df, device_option, browser_option)
slice_dice_df = slice_dice_df.groupby('date').sum().reset_index()
slice_dice_df['cookie_support_pct'] = (slice_dice_df.cookies_supported / slice_dice_df.traffic) * 100

best_fit_slice_dice = line_of_best_fit(slice_dice_df.date.to_list(), slice_dice_df.cookie_support_pct.to_list())
st.pyplot(
    plot_stat_by_date(
        slice_dice_df.date,
        slice_dice_df.cookie_support_pct,
        best_fit_slice_dice)[0])

st.markdown(
    """    
    **Warning!** Selecting a cross that does not exist for example Mobile and IE, will return a strange graph.

    _You can select the checkbox below to see the filtered dataframe._
    """
)

show_me = st.checkbox('Show me the data!')
if show_me:
    st.write(slice_dice_df)


st.subheader('Why does `Firefox` yield such high cookie support %?')

st.markdown(
    """    
    This is due to how different browsers decide on what 3rd party cookies to accept. Firefox uses a **known trackers list**. Our approach
    to collecting this data is done actively, meaning we try to set and then read a cookie. This method allows to understand the changing behavior
    of users within a single browser, as it picks up on settings changes.
    """
)

st.header('About AirGrid')

st.markdown(
    """    
    **[AirGrid](https://airgrid.io) is a privacy-first audience platform.**

    Our vision is to make web ads more private, by allowing people to retain control over their own data. We do this by
    shifting the audience modelling to run directly on the individual's device.

    ✉️ Drop us a line to say hello `hello [AT] airgrid.io`

    **References**:
    - [AirGrid](https://airgrid.io)
    - [EdgeKit](https://edgekit.org)
    - [Blog Post](https://medium.com/@ag_internal/cookie-support-analysis-in-the-airgrid-blog-network)
    - [Raw data for this app](https://storage.googleapis.com/ag-external-data/airgrid_blog_network_cookie_support.csv)
    - [Code for this app](https://github.com/AirGrid/external-analytics/tree/main/streamlit)
    """
)