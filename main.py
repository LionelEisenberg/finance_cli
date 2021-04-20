from dateutil.parser import parse
import csv
import matplotlib.pyplot as plt
from datetime import date, datetime, timedelta
from tabulate import tabulate
import matplotlib.animation as animation
from stock import Stock
import click
import time
import yfinance as yf
import pandas as pd

numStocks = 7

class Portfolio:
    def __init__(self, stocks):
        self.stocks = {}
        for stock in stocks:
            self.stocks[stock.ticker] = stock

    def getPorfolioCurr(self):
        curr = 0
        for stock in self.stocks.values():
            curr += stock.getCurrentPrice() * stock.numShares
        return curr

    def getPorfolioOriginal(self):
        orig = 0
        for stock in self.stocks.values():
            orig += stock.origInvested
        return orig

    def getPorfolioCloseYest(self):
        closeYest = 0
        for stock in self.stocks.values():
            closeYest += stock.getYesterdaysClose() * stock.numShares
        return closeYest


    def gainsSinceDate(self, date="2010-01-01", percentageBool=False, ticker=""):
        totalAtStart, totalNow = 0, 0
        for stock in self.stocks:
            if ticker == "" or ticker == stock.ticker:
                startDate = date
                if isinstance(startDate, str):
                    startDate = parse(date)
                if startDate < stock.dateOfPurchase:
                    startDate = stock.dateOfPurchase
                    _, sharePriceNow = stock.sharePriceDifferenceSinceDate(startDate)
                    sharePriceAtDate = stock.origSharePrice
                else :
                    sharePriceAtDate, sharePriceNow = stock.sharePriceDifferenceSinceDate(startDate)
                totalAtStart += sharePriceAtDate * stock.numShares
                totalNow += sharePriceNow * stock.numShares
        if percentageBool:
            return (totalNow / totalAtStart - 1) * 100
        else:
            return totalNow - totalAtStart



    def getMainData(self):
        data = []
        for stock in self.stocks:
            dataLine = []
            dataLine.append(stock.ticker)
            dataLine.append(self.gainsSinceDate(stock.dateOfPurchase,True, ticker=stock.ticker))
            dataLine.append(self.gainsSinceDate(stock.dateOfPurchase,ticker=stock.ticker))
            dataLine.append(self.gainsSinceDate(datetime.now() - timedelta(days=1),True, ticker=stock.ticker))
            dataLine.append(self.gainsSinceDate(datetime.now() - timedelta(days=1),ticker=stock.ticker))
            dataLine.append(stock.getCurrentPrice())
            data.append(dataLine)
        dataLine = []
        dataLine.append("TOTAL")
        dataLine.append(self.gainsSinceDate(stock.dateOfPurchase,True))
        dataLine.append(self.gainsSinceDate(stock.dateOfPurchase))
        dataLine.append(self.gainsSinceDate(datetime.now(), True))
        dataLine.append(self.gainsSinceDate(datetime.now()))
        dataLine.append("######")
        data.append(dataLine)
        return data

    def getTodaysChart(self, ticker, interval):
        if ticker == "TOTAL":
            x, y = self.stocks[0].getTodaysData(interval)
            y *= self.stocks[0].numShares
            for i in range(1, len(self.stocks)):
                _, z = self.stocks[i].getTodaysData(interval)
                y +=  z * self.stocks[i].numShares
            return x, y
        for stock in self.stocks:
            if stock.ticker == ticker:
                return stock.getTodaysData(interval)

    def getTotalChart(self, ticker):
        if ticker == "TOTAL":
            x, y = self.stocks[0].getTotalData()
            y *= self.stocks[0].numShares
            for i in range(1, len(self.stocks)):
                _, z = self.stocks[i].getTotalData()
                y +=  z * self.stocks[i].numShares
            return x, y
        for stock in self.stocks:
            if stock.ticker == ticker:
                return stock.getTotalData()

    def getPorfolioDiversity(self):
        y = []
        labels = []
        for stock in self.stocks:
            totalPrice = stock.getCurrentPrice() * stock.numShares
            y.append(totalPrice)
            labels.append(stock.ticker)
        return y, labels

    def getMainDataV2(self):
        data = []
        for stock in self.stocks.values():
            dataLine = []
            dataLine.append(stock.ticker)
            dataLine.append(stock.getTotalGainInDollars())
            dataLine.append(stock.getTotalGainInPercentage())
            dataLine.append(stock.getTodaysGainInDollars())
            dataLine.append(stock.getTodaysGainInPercentage())
            dataLine.append(stock.getCurrentPrice())
            data.append(dataLine)
        dataLine = []
        dataLine.append("TOTAL")
        gainsTotalDollar, gainsTotalPercentage, gainsTodayDollar, gainsTodayPercentage = 0, 0, 0, 0
        for dl in data:
            gainsTotalDollar += dl[1]
            gainsTodayDollar += dl[3]
        dataLine.append(gainsTotalDollar)
        dataLine.append((self.getPorfolioCurr()/self.getPorfolioOriginal() - 1) *100)
        dataLine.append(gainsTodayDollar)
        dataLine.append((self.getPorfolioCurr()/self.getPorfolioCloseYest() - 1) *100)
        dataLine.append("######")
        data.append(dataLine)
        return data


@click.group()
def main():
    click.echo("Welcome to finance CLI")

@main.command()
def mainData():
    starttime = time.time()
    portfolio = importData()
    data = portfolio.getMainDataV2()
    click.echo((tabulate(data, headers=["Ticker", "Total $", "Total %", "Today $", "Today %", "Share price"])))

    while True:
        time.sleep(20.0)
        portfolio = importData()
        data = portfolio.getMainDataV2()
        click.echo((tabulate(data)))


@main.command()
@click.argument('ticker')
def todaysChart(ticker):
    portfolio = importData()

    if ticker == "ALL":
        fig, axs = plt.subplots(2, 4)
        counter = 0
        for row in axs:
            for col in row:
                if counter >= 7:
                    continue
                stock = portfolio.stocks[counter]
                print(stock.ticker)
                x, y = portfolio.getTodaysChart(stock.ticker, 5)
                col.plot(x, y)
                col.set_title(stock.ticker)
                col.get_xaxis().set_visible(False)
                counter += 1
        plt.show()

    else:
        x, y = portfolio.getTodaysChart(ticker, 5)

        fig, ax = plt.subplots()
        plt.plot(x, y)

        for n, label in enumerate(ax.xaxis.get_ticklabels()):
            if n % 12 != 0:
                label.set_visible(False)

        plt.title("Performance for ticker " + ticker + " today")
        plt.xlabel("date")
        plt.ylabel("price ($)")
        plt.show()

@main.command()
@click.argument('ticker')
def liveChart(ticker):
    portfolio = importData()

    if ticker == "ALL":
        fig, axs = plt.subplots(2, 4)

        def animate(i):
            counter = 0
            for row in axs:
                for col in row:
                    if counter >= 7:
                        continue
                    stock = portfolio.stocks[counter]
                    x, y = portfolio.getTodaysChart(stock.ticker, 5)
                    col.clear()
                    col.plot(x, y)
                    col.set_title(stock.ticker + ": " + str(round(y[-1], 2)))
                    col.get_xaxis().set_visible(False)
                    counter += 1

        ani = animation.FuncAnimation(fig, animate, interval=5000)
        plt.show()
    else:
        fig, ax = plt.subplots()

        def animate(i):
            x, y = portfolio.getTodaysChart(ticker, 1)
            ax.clear()
            ax.plot(x, y)

            for n, label in enumerate(ax.xaxis.get_ticklabels()):
                if n % 12 != 0:
                    label.set_visible(False)

        plt.title("Performance for ticker " + ticker + " today")
        plt.xlabel("date")
        plt.ylabel("price ($)")
        ani = animation.FuncAnimation(fig, animate, interval=1000)
        plt.show()


@main.command()
def diversity():
    portfolio = importData()
    y, labels = portfolio.getPorfolioDiversity()
    explode = [0.05] * len(portfolio.stocks)
    plt.pie(y, labels=labels, autopct='%1.2f%%', explode = explode)
    plt.show()

@main.command()
@click.argument('ticker')
def totalChart(ticker):
    portfolio = importData()
    plt.plot(portfolio.getTotalChart(ticker))
    if ticker == "TOTAL":
        ticker = "All Stocks"
    plt.title("Performance for " + ticker + " in total")
    plt.xlabel("date")
    plt.ylabel("price ($)")
    plt.show()

@main.command()
def test():
    print(yf.Ticker("VTI").info)

def importData():
    stocks = []
    with open('info.csv') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter='\t')
        for row in csv_reader:
            stocks.append(Stock(row))

    return Portfolio(stocks)

if __name__ == '__main__':
    main()
