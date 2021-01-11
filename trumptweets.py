import json
from dateutil.parser import parse
import time
from statistics import mean, median
import numpy as np
import humanize

ONLY_POTUS = True # Only analyze POTUS Tweets
POTUS_DATE = '2016-10-08' # Aprox election results datetime
PRUNE_DELETED = False

def getTweets(onlyPotus, pruneDeleted):
    # 1. Download the JSON archive (latest is Nov 2020 though) -->  https://drive.google.com/file/d/1ZGFVJvEgEjLwjhABx2kgt4BrZRCcu3qR/view
    # 2. Use realtime filter to get the missing tweets (max 2000 results) -->  https://www.thetrumparchive.com/?dates=%5B%222020-11-05%22%2C%222021-01-31%22%5D
    fname1 = 'tweets_11-06-2020.json' # date in here is '%Y-%m-%d %H:%M:%S
    fname2 = 'tweets_after_11-06-2020.json' # date in here is of milisecond epoch form 
    with open(fname1, 'r') as f1:
        tweets1 = json.load(f1)
    with open(fname2, 'r') as f2:
        tweets2 = json.load(f2)
    # Convert date format to match
    tmp=[]
    for t in tweets2:
        d = t.get("date") / 1000
        t["date"] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(d))
    tweets_combined = tweets1 + tweets2 #sorted(tweets1 + tweets2, key=lambda k: k['date']) 
    # Remove duplicates from overlap. This seems tricky as the IDs don't match between the two sets, and there are duplicates on the timestamps. Timestamps probably
    #  reflect capture time, not tweet time. So, we contruct a UID as text+date
    tmp=[]
    dup=[]
    idcache={}
    for t in tweets_combined:
        uid = t.get("text") + t.get("date")
        if uid not in idcache:
            tmp.append(t)
        else:
            dup.append(t)
        idcache[uid] = 1
    tweets = tmp
    print("[+] Loaded {} Tweets from @realDonaldTrump".format(len(tweets)))
    if onlyPotus:
        tmp = []
        for t in tweets:
            if t.get("date") > POTUS_DATE:
                tmp.append(t)
        print("[+] Pruned {} Tweets for post-POTUS Tweets only".format(len(tweets) - len(tmp)))
        tweets = tmp
    if pruneDeleted:
        tmp = []
        for t in tweets:
            if t.get("isDeleted") == 'f' or "isDeleted" not in t: #Not all Tweets have the "isDeleted" flag, which was hard to debug...
                tmp.append(t)
        print("[+] Pruned {} deleted Tweets".format(len(tweets) - len(tmp)))
        tweets = tmp
    print("[+] Loaded {} Tweets from @realDonaldTrump".format(len(tweets)))
    tweets = sorted(tweets, key=lambda k: k['date']) # Sort
    return tweets

if __name__ == "__main__":
    tweets = getTweets(ONLY_POTUS, PRUNE_DELETED)
    deltas = []
    maxDelta = 0
    maxDeltaTweet = ''
    maxDeltaTweetNext = ''
    for i in range(len(tweets)-1):
        t1 = parse(tweets[i].get("date"))
        t2 = parse(tweets[i+1].get("date"))
        delta = (t2-t1).total_seconds() # Seconds between tweets
        deltas.append(delta)
        if delta > maxDelta:
            maxDelta = delta
            maxDeltaTweet = tweets[i]
            maxDeltaTweetNext = tweets[i+1]
    meanTD = mean(deltas)
    medianTD = median(deltas)
    #print("[+] Max time between tweets: {}".format(humanize.naturaldelta(maxDelta)))
    print("[+] Longest delay between tweeting ({}) after this tweet : \"{}\" ({})".format(humanize.naturaldelta(maxDelta), maxDeltaTweet.get("text"), maxDeltaTweet.get("date")))
    print("[+] Tweet after that big delay: \"{}\" ({})".format(maxDeltaTweetNext.get("text"), maxDeltaTweetNext.get("date")))
    print("[+] Mean time between tweets: {}".format(humanize.naturaldelta(meanTD)))
    print("[+] Median time between tweets: {}".format(humanize.naturaldelta(medianTD)))

    #####################
    # Let's plot it     #
    #####################
    import matplotlib.pyplot as plt
    from numpy.random import normal
    from matplotlib.ticker import ScalarFormatter, FuncFormatter
    from matplotlib.offsetbox import (TextArea, DrawingArea, OffsetImage,
                                  AnnotationBbox)

    # Setup axes
    fig, axes = plt.subplots(2, 1, figsize=(12,8))
    fig.suptitle("Analysis of @realDonaldTrump's Tweeting Frequency", fontsize=12, fontweight='bold')

    # 1. First graph, Trump's last 500 Tweets
    last=156
    data = [int(e/60) for e in deltas[-last:]]
    ax1 = axes[0]
    #data = deltasS[-last:]
    ax1.plot(data, '-bo',markersize=4)
    #ax1.plot(data)
    ax1.set_title("Time Between Last {} Tweets".format(last))
    #ax1.set_xlabel("Last {} tweets".format(last))
    ax1.set_ylabel("Minutes between tweets")
    ax1.grid(True, linestyle='dotted')

    # Get timestamps for last 500 tweets
    lastTweets = tweets[-last:]
    #lastTweetDates = [parse(d.get("date")).strftime("%d %b, %H:%M:%S") for d in lastTweets]
    lastTweetDates = [parse(d.get("date")).strftime("%d %b") for d in lastTweets]

    # Super dangerous hack to print dates
    def limitLaster(x):
        if x<0:
            return 0
        if x >= last:
            return last-1
        return x
    ax1.get_xaxis().set_major_formatter(FuncFormatter(lambda x, p: lastTweetDates[int(limitLaster(x))]))

    ax1.set_xticks([-20,   0,  40, 60,  100, 120, 140, 160, 180]) # Manual date hack to get one tick per day for Janunary


    # Let's add an extra axis on the right with hours
    data = [(e/60) for e in data]    # to hours
    for d in data:
        d = int(d/60)
    ax2 = ax1.twinx()
    ax2.plot(data, alpha=0.0, color='red') # Set trasparency so we don't actually plot the data, just want the extra y axis on the right
    ax2.tick_params(axis='y')
    ax2.set_ylabel("Hours between tweets")

    # Some annotations
    jan3 = tweets[-104:-62] # jan 3 was a busy day
    offsetbox = TextArea("Jan 3 was a busy day; forty tweets,\nonly two mins between each", minimumdescent=False)
    xy = (77, 300)
    ab = AnnotationBbox(offsetbox, xy,
                        xybox=(0, 50),
                        xycoords='data',
                        boxcoords="offset points",
                        arrowprops=dict(arrowstyle="->"))
    ax1.add_artist(ab)


    offsetbox = TextArea("Temporary ban", minimumdescent=False)
    xy = (152, 1500)
    ab = AnnotationBbox(offsetbox, xy,
                        xybox=(-50, -40),
                        xycoords='data',
                        boxcoords="offset points",
                        arrowprops=dict(arrowstyle="->"))
    ax1.add_artist(ab)




    ##### Second plot
    # Seconds to hours
    deltasH = []
    for d in deltas:
        deltasH.append(int(d / 60 / 60))

    ####
    ax2 = axes[1]
    binwidth=5
    bins=range(min(deltasH), max(deltasH) + binwidth, binwidth)
    ax2.hist(deltasH, bins=bins, edgecolor='black', linewidth=1.2) #, orientation='horizontal')#, align='left')
    start, end = ax2.get_xlim()
    ax2.xaxis.set_ticks(np.arange(min(deltasH), max(deltasH)+1, 5))
    ax2.set_yscale('log')
    ax2.yaxis.set_major_formatter(ScalarFormatter())
    ax2.yaxis.set_major_formatter(ScalarFormatter())
    ax2.set_ylim([1,100000]) # Hack to keep the 24k label off the edge. Should probably get_ylim and set max as next order of magnitude
    ax2.set_title("Count of Duration Between All Tweets as President (8 Oct 2016 to 8 Jan 2021)")
    ax2.set_xlabel("Hours between tweets")
    ax2.set_ylabel("Count (logarithmic)")
    textstr = "Mean time between tweets: {}\nMedian time between tweets: {}".format(humanize.naturaldelta(meanTD), humanize.naturaldelta(medianTD))
    props = dict(boxstyle='square', alpha=0.5)
    # place a text box in upper left in axes coords
    ax2.text(0.70, 0.95, textstr, transform=ax2.transAxes,
    verticalalignment='top', bbox=props)
    # Add labels
    for rect in ax2.patches:
        spacing=5
        # Get X and Y placement of label from rect.
        y_value = rect.get_height()
        x_value = rect.get_x() + rect.get_width() / 2
        # Number of points between bar and label. Change to your liking.
        space = spacing
        # Vertical alignment for positive values
        va = 'bottom'
        # Use Y value as label and format number with one decimal place
        label = "{} tweets".format(int(y_value))
        # Create annotation
        ax2.annotate(
            label,                      # Use `label` as label
            (x_value, y_value),         # Place label at end of the bar
            xytext=(0, spacing),          # Vertically shift label by `space`
            textcoords="offset points", # Interpret `xytext` as offset in points
            ha='center',                # Horizontally center label
            va=va)    


    fig.tight_layout(pad=2.0)
    #plt.show()
    fig.savefig("TrumpTweets.png", bbox_inches='tight')
    print("[+] Graphs saved to 'TrumpTweets.png'")
