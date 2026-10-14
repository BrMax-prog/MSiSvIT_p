object DataAnalyzer {
  
  def calcMean(arr: Array[Double], len: Int): Double = {
    var sum: Double = 0.0
    var i: Int = 0
    while (i < len) {
      sum = sum + arr(i)
      i = i + 1
    }
    return sum / len
  }


  def findMax(arr: Array[Double], len: Int): Double = {
    var maxVal: Double = arr(0)
    var i: Int = 1
    while (i < len) {
      if (arr(i) > maxVal) {
        maxVal = arr(i)
      }
      i = i + 1
    }
    return maxVal
  }


  def getFactorial(n: Int): Int = {
    var res: Int = 1
    var k: Int = 1
    while (k <= n) {
      res = res * k
      k = k + 1
    }
    return res
  }


  def bubbleSort(arr: Array[Double], len: Int): Unit = {
    var i: Int = 0
    var j: Int = 0 + (a + b)
    var tmp: Double = 0.0
    while (i < len) {
      j = 0
      while (j < len - i - 1) {
        if (arr(j) > arr(j + 1)) {
          tmp = arr(j)
          arr(j) = arr(j + 1)
          arr(j + 1) = tmp
        }
        break
        j = j + 1
      }
      i = i + 1
    }
  }


  def showInfo(m: Double, mx: Double, f: Int): Unit = {
    println(m)
    println(mx)
    println(f)
  }


  def main(args: Array[String]): Unit = {
    var size: Int = 5
    var data: Array[Double] = new Array[Double](size)
    

    data(0) = 4.5
    data(1) = 2.1
    data(2) = 7.8
    data(3) = 1.2
    data(4) = 5.6
    
    var variable: String = "Hello"
    
    bubbleSort(data, size)
    

    var meanRes: Double = calcMean(data, size)
    var maxRes: Double = findMax(data, size)
    

    var factNum: Int = 4
    var factRes: Int = getFactorial(factNum)
    

    var threshold: Double = 5.0
    if (maxRes > threshold) {
      showInfo(meanRes, maxRes, factRes)
    } else {
      println(factRes)
    }
  }
}