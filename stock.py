from dateutil.parser import parse
from datetime import date, datetime
import yfinance as yf

class Stock:
    def __init__(self, entry):
        self.ticker = entry[0]
        self.origInvested = float(entry[1])
        self.origSharePrice = float(entry[2])
        self.dateOfPurchase = parse(entry[3])
        self.numShares = float(entry[4])
        self.tickerData = yf.Ticker(self.ticker)
        self.info = self.tickerData.info

    def __repr__(self):
        return "ticker={0},origInvested={1},origSharePrice={2},dateOfPurchase={3},numShares={4}".format(self.ticker,self.origInvested ,self.origSharePrice, self.dateOfPurchase, self.numShares)

    def getTickerData(self):
        return "tickerData={0}".format(self.tickerData)

    def sharePriceDifferenceSinceDate(self, startDate):
        tickerDf = self.tickerData.history(period="1d",start=startDate)
        return tickerDf['Close'][0], tickerDf['Close'][-1]

    def getTodaysData(self, interval):
        tickerDf = self.tickerData.history(period="1d",interval=str(interval) + "m")
        return tickerDf["High"].keys().strftime("%H-%M"), tickerDf["High"].values

    def getCurrentPrice(self):
        return self.info['regularMarketPrice']

    def getYesterdaysClose(self):
        return self.info['regularMarketPreviousClose']

    def getTotalData(self):
        tickerDf = self.tickerData.history(start=self.dateOfPurchase,period="1d",interval="1h")
        return tickerDf["High"]

    def getTotalGainInDollars(self):
        currentAmount = self.getCurrentPrice() * self.numShares
        return currentAmount - self.origInvested

    def getTotalGainInPercentage(self):
        currentAmount = self.getCurrentPrice() * self.numShares
        return (currentAmount / self.origInvested - 1) *100

    def getTodaysGainInDollars(self):
        currentAmount = self.getCurrentPrice() * self.numShares
        yestClose = self.getYesterdaysClose() * self.numShares
        return currentAmount - yestClose

    def getTodaysGainInPercentage(self):
        currentAmount = self.getCurrentPrice() * self.numShares
        yestClose = self.getYesterdaysClose() * self.numShares
        return (currentAmount / yestClose - 1) * 100
