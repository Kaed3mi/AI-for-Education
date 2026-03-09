// 作业数据：每次作业包含多道题，每道题有题目描述和测试用例
// 此文件独立存放作业题目与测试点，方便维护和扩展
const HOMEWORK_DATA = {
    'homework0': {
        name: '25级程序设计基础练习（不算入成绩）',
        problems: [
            {
                title: '1.可逆素数判断',
                description: `## 编程题目

**题目描述：** 若将某一素数的各位数字的顺序颠倒后得到的数仍是素数，则此素数称为可逆素数。编写一个判断某数是否可逆素数的函数，在主函数中输入一个整数，再调用此函数进行判断。

**输入形式：** 用户在第一行输入一个整数。

**输出形式：** 程序在下一行输出yes或是no，yes表示此数是可逆素数，no表示不是。用户输入的数必须为正整数。注意：yes或是no全是小写输出。

**样例输入：**
\`\`\`
23
\`\`\`

**样例输出：**
\`\`\`
no
\`\`\`

**样例说明：** 用户输入23，23各位数字颠倒之后得到32，23是素数，但32不是素数，所以23不是可逆素数。

**评分标准：** 结果完全正确得20分，每个测试点4分。提交程序名为：getprimenum.c`,
                testCases: [
                    { input: '13', expected_output: 'yes' },
                    { input: '29', expected_output: 'no' },
                    { input: '70', expected_output: 'no' },
                    { input: '14', expected_output: 'no' },
                    { input: '5', expected_output: 'yes' }
                ]
            },
            {
                title: '2.矩形相交面积',
                description: `## 编程题目

**题目描述：** 平面上有两个矩形A和B，其位置是任意的。编程求出其相交部分（如图中阴影部分）的面积。（0≤a，b≤1000）

**输入形式：** 从标准输入读取两行以空格分隔的整数，格式如下：
Ax1 Ay1 Ax2 Ay2
Bx1 By1 Bx2 By2
其中（x1，y1）和（x2，y2）为矩形对角线上端点的坐标。各坐标值均为整数，取值在0至1000之间。

**输出形式：** 向标准输出打印一个整数，是两矩形相交部分的面积（可能为0）。

**输入样例：**
\`\`\`
0 0 2 2
1 1 3 4
\`\`\`

**输出样例：**
\`\`\`
1
\`\`\`

**提示：** 输入的两点可以是矩形任一对角线上的端点，求相交的面积可以先求矩形在X轴和Y轴上的交集。矩形在X轴上的交集可以按照如下算法进行求解：假设AX1和AX2中的较大值为MAX_AX，较小值为MIN_AX；BX1和BX2中的较大值为MAX_BX，较小值为MIN_BX。用MAX_AX和MAX_BX中的较小者减去MIN_AX和MIN_BX中的较大者，结果为正表示两矩形在X轴上的交集，若为负则表示不相交。

**评分标准：** 结果完全正确得20分，每个测试点4分，提交程序文件名为area.c。`,
                testCases: [
                    { input: '0 2 2 0\n1 4 3 1', expected_output: '1' },
                    { input: '500 500 750 450\n2 3 100 100', expected_output: '0' },
                    { input: '0 100 110 90\n50 60  70 30', expected_output: '0' },
                    { input: '0 900 500 300\n10 890 490 400', expected_output: '235200' },
                    { input: '100 500 200 450\n110 490 190 150', expected_output: '3200' }
                ]
            },
            {
                title: '3.求差集',
                description: `## 编程题目

**题目描述：** 两个集合的差集定义如下：集合 A、B 的差集，由所有属于 A 但不属于 B 的元素构成。输入两个集合 A、B，每个集合中元素都是自然数。求集合 A、B 的差集。

**输入形式：** 从标准输入接收集合中的自然数元素，以空格分隔。-1 表示输入结束。其中，每个集合都不输入重复的元素。

**输出形式：** 输出差运算后集合中的元素，以空格分隔。输出元素的顺序与原有集合 A 输入的顺序一致。如果 A、B 的差集为空集，则不输出任何数值。

**样例输入：**
\`\`\`
2 8 3 4 -1
6 1 4 9 -1
\`\`\`

**样例输出：**
\`\`\`
2 8 3
\`\`\`

**样例说明：** 从标准输入接收集合中的自然数元素，输出集合 A、B 的差集。

**评分标准：** 该题要求输出差运算后集合中的元素，结果完全正确得 20 分，每个测试点 4 分。上传 C 语言文件名为 sets.c。`,
                testCases: [
                    { input: '2 4 6 8 -1\n3 5 7 8 -1', expected_output: '2 4 6' },
                    { input: '2 3 4 5 6 -1\n1 8 9 -1', expected_output: '2 3 4 5 6' },
                    { input: '2 3 4 5 7 -1\n3 8 9 1 -1', expected_output: '2 4 5 7' },
                    { input: '2 3 4 5 -1\n2 3 5 -1', expected_output: '4' },
                    { input: '1 2 3 4 -1\n5 6 7 -1', expected_output: '1 2 3 4' }
                ]
            },
            {
                title: '4.矩阵运算',
                description: `## 编程题目

**题目描述：** 对于多个 N 阶矩阵，依次进行加、减运算。

**输入形式：** 从标准输入读取输入。第一行只有一个整数 N（1<=N<=10），代表矩阵的阶数。接下来是一个矩阵，是 N 行，每行有 N 个整数（可能是正、负整数），是矩阵的所有元素。然后一行只含一个字符 "+" 或 "-"，代表加、减操作。然后用同样的方式输入另一个矩阵。后续仍然是运算符和矩阵。直至运算符为 "#" 时停止计算，将结果输出。

**输出形式：** 向标准输出打印矩阵的操作结果。输出 N 行，每行对应矩阵在该行上的所有元素，每一行末均输出一个回车符。每个元素占 5 个字符宽度（包括负号），向右对齐，不足部分补以空格。

**输入样例：**
\`\`\`plaintext
3
1 -2 7
2 8 -5
3 6 9
+
3 5 7
-1 2 6
3 7 10
-
1 -2 7
2 8 -5
3 6 9
#
\`\`\`

**输出样例：**（#代表空格）
\`\`\`
    3    5    7
   -1    2    6
    3    7   10
\`\`\`

**评分标准：** 本题不准使用数学库函数。运行时限 1 秒，完全正确 20 分，每个测试点 4 分。提交程序文件名为 matrix.c。`,
                testCases: [
                    { input: '3\n1 -2 7\n2 8 -5\n3 6 9\n+\n3 5 7\n-1 2 6\n3 7 10\n-\n1 -2 7\n2 8 -5\n3 6 9\n#', expected_output: '    3    5    7\n   -1    2    6\n    3    7   10' },
                    { input: '3\n1 2 3\n4 5 6\n7 8 9\n+\n1 2 3\n4 5 6\n7 8 9\n-\n1 2 3\n4 5 6\n7 8 9\n#', expected_output: '    1    2    3\n    4    5    6\n    7    8    9' },
                    { input: '2\n-1 2\n3 4\n-\n3 4\n5 6\n+\n1 1\n1 1\n#', expected_output: '   -3   -1\n   -1   -1' },
                    { input: '1\n2\n+\n3\n-\n9\n#', expected_output: '   -4' },
                    { input: '9\n2 1 4 7 6 8 10 4 2\n3 2 2 2 1 1 2 3 4\n6 2 5 6 7 8 9 0 9\n2 5 7 9 5 8 6 4 2\n2 2 3 5 7 8 9 0 2\n3 5 6 8 9 0 2 2 2\n2 2 2 2 2 2 2 2 2\n3 4 4 4 4 4 4 4 4\n1 2 3 4 5 6 7 7 8\n+\n2 1 4 7 6 8 10 4 2\n3 2 2 2 1 1 2 3 4\n6 2 5 6 7 8 9 0 9\n2 5 7 9 5 8 6 4 2\n2 2 3 5 7 8 9 0 2\n3 5 6 8 9 0 2 2 2\n2 2 2 2 2 2 2 2 2\n3 4 4 4 4 4 4 4 4\n1 2 3 4 5 6 7 7 8\n-\n2 1 4 7 6 8 10 4 2\n3 2 2 2 1 1 2 3 4\n6 2 5 6 7 8 9 0 9\n2 5 7 9 5 8 6 4 2\n2 2 3 5 7 8 9 0 2\n3 5 6 8 9 0 2 2 2\n2 2 2 2 2 2 2 2 2\n3 4 4 4 4 4 4 4 4\n1 2 3 4 5 6 7 7 8\n#', expected_output: '    2    1    4    7    6    8   10    4    2\n    3    2    2    2    1    1    2    3    4\n    6    2    5    6    7    8    9    0    9\n    2    5    7    9    5    8    6    4    2\n    2    2    3    5    7    8    9    0    2\n    3    5    6    8    9    0    2    2    2\n    2    2    2    2    2    2    2    2    2\n    3    4    4    4    4    4    4    4    4\n    1    2    3    4    5    6    7    7    8' }
                ]
            },
            {
                title: '5.文件拷贝',
                description: `## 编程题目

**题目描述：** 写一个程序将一个文件 fcopy.in 拷贝至另一个文件 fcopy.out，其中在所拷贝的文件中，多个连续空白符（包括空格符、制表符）只拷贝一个空格符，其它字符不变。

**输入形式：** 源文件名和目标文件名分别为 fcopy.in 和 fcopy.out，程序将从当前目录下读取 fcopy.in 文件。

**输出形式：** 将 fcopy.in 文件内容拷贝至当前目录下的 fcopy.out 文件中。在所拷贝的文件中，多个连续空白符（包括空格符、制表符）只拷贝一个空格符，若非空白符之间有一个制表符，则该制表符也要替换为空格符，其它字符不变。

**输入样例：** 假如文件 fcopy.in 中内容如下：
\`\`\`
Alcatel provides end-to-end solutions.
\`\`\`

**输出样例：** 输出文件 fcopy.out 中内容为：
\`\`\`
Alcatel provides end-to-end solutions.
\`\`\`

**样例说明：** 将文件 fcopy.in 拷贝到 fcopy.out，同时做适当的转换。

**评分标准：** 其中在所拷贝的文件中，多个连续空白符只拷贝一个空格符，完全符合要求得 20 分，每个测试点 4 分。提交程序名为 copy.c。

**注意：** 本题需要使用文件操作（读取 fcopy.in，写入 fcopy.out）。`,
                ioMode: 'file',
                inputFile: 'fcopy.in',
                outputFile: 'fcopy.out',
                testCases: [
                    { input: 'Alcatel             provides\tend-to-end solutions.', expected_output: 'Alcatel provides end-to-end solutions.' },
                    { input: 'It\tenables enterprises to deliver               content to any type of user.', expected_output: 'It enables enterprises to deliver content to any type of user.' },
                    { input: 'MS or Ph.D. candidate at\t\tschool.', expected_output: 'MS or Ph.D. candidate at school.' },
                    { input: 'Supervisor can approve an\t\tat least six-month period of full-time visiting', expected_output: 'Supervisor can approve an at least six-month period of full-time visiting' },
                    { input: 'smart and good\t\t\tat programming', expected_output: 'smart and good at programming' }
                ]
            },
            {
                title: '6.求两组整数的异或集',
                description: `## 编程题目

**题目描述：** 从标准输入中输入两组整数（每行不超过 20 个整数，每组整数中元素不重复），合并两组整数，去掉在两组整数中都出现的整数，并按从大到小顺序排序输出（即两组整数集"异或"）。

**输入形式：** 首先输入第一组整数，以一个空格分隔各个整数；然后在新的一行上输入第二组整数，以一个空格分隔，行末有回车换行。

**输出形式：** 按从大到小顺序排序输出合并后的整数集（去掉在两组整数中都出现的整数，以一个空格分隔各个整数）。

**样例输入：**
\`\`\`
5 1 4 32 8 7 9 -6
5 2 87 10 1
\`\`\`

**样例输出：**
\`\`\`
87 32 10 9 8 7 4 2 -6
\`\`\`

**样例说明：** 第一组整数为 5 1 4 32 8 7 9 -6，第二组整数分别为 5 2 87 10 1。将第一组和第二组整数合并（去掉在两组整数中都出现的整数 5 和 1），并从大到小顺序排序后得到对应结果。

**评分标准：** 该题要求输出两组整数的异或集，共有 5 个测试点，提交程序文件名为 xor.c。`,
                testCases: [
                    { input: '1\n2', expected_output: '2 1' },
                    { input: '1 3 2\n4 2 5 8', expected_output: '8 5 4 3 1' },
                    { input: '92 81 78 0\n7 81 92 6', expected_output: '78 7 6 0' },
                    { input: '3 5 4 2 1\n5 1', expected_output: '4 3 2' },
                    { input: '1 20 18 4 3 2 6 8 17 16 15 14 13 11 12 5 9 7 10 19\n10 9 8 7 6 5 4 3 2 1', expected_output: '20 19 18 17 16 15 14 13 12 11' }
                ]
            },
            {
                title: '7.凸多边形面积',
                description: `## 编程题目

**题目描述：** 给出平面上一组顶点的坐标，计算出它们所围成的凸多边形的面积。

**输入形式：** 从标准输入读取顶点坐标。格式为：第一行是点的个数 N（3≤N≤15），后面紧接着 N 行，每行两个数字（由空格隔开），分别表示该点的 X、Y 坐标（0≤X，Y≤32767）。所有点的坐标互不相同，且按顺时针次序给出。输入数据确保该多边形是一个凸多边形。

**输出形式：** 向标准输出打印一个浮点数，是该多边形的面积。该浮点数保留两位小数。

**输入样例：**
\`\`\`
4
3 3
3 0
1 0
1 2
\`\`\`

**输出样例：**
\`\`\`
5.00
\`\`\`

**样例说明：** 输入数据表示了对应的四边形，其面积为 5.00。

**提示：** 求三角形面积可用海伦公式，求平方根可用 <math.h> 头文件中定义的 sqrt 函数。

**评分标准：** 结果完全正确得 20 分，每个测试点 4 分。提交程序名为：points.c。`,
                testCases: [
                    { input: '4\n3 3\n3 0\n1 0\n1 2', expected_output: '5.00' },
                    { input: '3\n100 0\n0 100\n200 200', expected_output: '15000.00' },
                    { input: '5\n2 13\n60 20\n99 15\n99 8\n70 2', expected_output: '984.50' },
                    { input: '8\n0 200\n100 300\n200 300\n300 200\n300 100\n200 0\n100 0\n0 100', expected_output: '70000.00' },
                    { input: '10\n0 20\n10 30\n20 40\n30 40\n40 30\n40 20\n30 10\n20 0\n10 0\n0 10', expected_output: '1100.00' }
                ]
            },
            {
                title: '8.整数的N进制字符串表示',
                description: `## 编程题目

**题目描述：** 编写函数 itob(n,s,b)，用于把整数 n 转换成以 b 为基的字符串并存储到 s 中。编写程序，使用函数 itob(n,s,b) 将输入的整数 n，转换成字符串 s，将 s 输出。转换后的字符串从最高的非零位开始输出。如果 n 为负数，则输出的字符串的第一个字符为'-'。b 为大于 1 小于 37 的任意自然数值。当 b=2 时，输出字符只可能是'0'和'1'；当 b=16 时，输出字符串中可能含有字符为'0'-'9'，'a'-'f'（字母以小写输出）。b 还可以是其它数值。比如输入 n=33，b=17，则输出 33 的 17 进制值为 "1g"。

**输入形式：** 控制台输入整数 n 和 b，其中 n 可以为负数。n 和 b 以空格分隔。

**输出形式：** 控制台输出转化后的字符串 s。

**样例输入：**
\`\`\`
5 2
\`\`\`

**样例输出：**
\`\`\`
101
\`\`\`

**样例说明：** 5 的二进制就是 101。

**评分标准：** 结果完全正确得 20 分，每个测试点 4 分。提交程序名为：itob.c。`,
                testCases: [
                    { input: '15 5', expected_output: '30' },
                    { input: '256 2', expected_output: '100000000' },
                    { input: '-8 8', expected_output: '-10' },
                    { input: '350 10', expected_output: '350' },
                    { input: '256 16', expected_output: '100' }
                ]
            },
            {
                title: '9.最长升序子串（选做）',
                description: `## 编程题目（选做，不计分）

**题目描述：** 输入一行字符串，该字符串只由小写英文字母 a-z 组成，且其中的字符可以重复，最长不超过 10000 个字符。从该字符串中按顺序挑选出若干字符（不一定相邻）组成一个新串，称为"子串"。如果子串中每两个相邻的字符或者相等，或者后一个比前一个大，则称为"升序子串"。编程求出输入字符串的最长升序子串的长度。例如，由输入字符串 abdbch 可以构成的升序子串有：abd、abch、bbch、abbch 等。其中最长的升序子串是 abbch，其长度为 5。

**输入形式：** 从标准输入读取一行字符串，该串不含空格，以回车符结束。

**输出形式：** 向标准输出打印一个正整数，是字符串中最长的升序子串的长度，在行末要输出一个回车符。

**输入样例：**
\`\`\`
abdbch
\`\`\`

**输出样例：**
\`\`\`
5
\`\`\`

**样例说明：** abdbch 中最长子串是 abbch，长度是 5。

**评分标准：** 结果完全正确得 20 分，每个测试点 4 分。上传 C 语言源程序为 up.c。`,
                testCases: [
                    { input: 'abdbch', expected_output: '5' },
                    { input: 'bcdhijlaijfsadfkjlsdfjkipqerpipvcnmasdfy', expected_output: '15' },
                    { input: 'aaaaaaaaaaaaaaaaaaaaaaaaabbbbbbbbbbbbbbbbbbcccccccccccccccdddddddddddddeeeeeeeeeeeeeeeyyyyyyyyyyyyy', expected_output: '99' },
                    { input: 'abc', expected_output: '3' },
                    { input: 'asdfpuqrpijkafzvjkvuhafisopqrewuopadsfjhvagjhfajafvhzjafqpoieurpguatqohvjafsdjzjvjaflhjqwreoyquqpzasdfpuqrpijkafzvjkvuhafisopqrewuopadsfjhvagjhfajafvhzjafqpoieurpguatqohvjafsdjzjvjaflhjqwreoyquqpzasdfpuqrpijkafzvjkvuhafisopqrewuopadsfjhvagjhfajafvhzjafqpoieurpguatqohvjafsdjzjvjaflhjqwreoyquqpzasdfpuqrpijkafzvjkvuhafisopqrewuopadsfjhvagjhfajafvhzjafqpoieurpguatqohvjafsdjzjvjaflhjqwreoyquqpzasdfpuqrpijkafzvjkvuhafisopqrewuopadsfjhvagjhfajafvhzjafqpoieurpguatqohvjafsdjzjvjaflhjqwreoyquqpzasdfpuqrpijkafzvjkvuhafisopqrewuopadsfjhvagjhfajafvhzjafqpoieurpguatqohvjafsdjzjvjaflhjqwreoyquqpzasdfpuqrpijkafzvjkvuhafisopqrewuopadsfjhvagjhfajafvhzjafqpoieurpguatqohvjafsdjzjvjaflhjqwreoyquqpzasdfpuqrpijkafzvjkvuhafisopqrewuopadsfjhvagjhfajafvhzjafqpoieurpguatqohvjafsdjzjvjaflhjqwreoyquqpzasdfpuqrpijkafzvjkvuhafisopqrewuopadsfjhvagjhfajafvhzjafqpoieurpguatqohvjafsdjzjvjaflhjqwreoyquqpzasdfpuqrpijkafzvjkvuhafisopqrewuopadsfjhvagjhfajafvhzjafqpoieurpguatqohvjafsdjzjvjaflhjqwreoyquqpzasdfpuqrpijkafzvjkvuhafisopqrewuopadsfjhvagjhfajafvhzjafqpoieurpguatqohvjafsdjzjvjaflhjqwreoyquqpzasdfpuqrpijkafzvjkvuhafisopqrewuopadsfjhvagjhfajafvhzjafqpoieurpguatqohvjafsdjzjvjaflhjqwreoyquqpzasdfpuqrpijkafzvjkvuhafisopqrewuopadsfjhvagjhfajafvhzjafqpoieurpguatqohvjafsdjzjvjaflhjqwreoyquqpzasdfpuqrpijkafzvjkvuhafisopqrewuopadsfjhvagjhfajafvhzjafqpoieurpguatqohvjafsdjzjvjaflhjqwreoyquqpzasdfpuqrpijkafzvjkvuhafisopqrewuopadsfjhvagjhfajafvhzjafqpoieurpguatqohvjafsdjzjvjaflhjqwreoyquqpzasdfpuqrpijkafzvjkvuhafisopqrewuopadsfjhvagjhfajafvhzjafqpoieurpguatqohvjafsdjzjvjaflhjqwreoyquqpzasdfpuqrpijkafzvjkvuhafisopqrewuopadsfjhvagjhfajafvhzjafqpoieurpguatqohvjafsdjzjvjaflhjqwreoyquqpzasdfpuqrpijkafzvjkvuhafisopqrewuopadsfjhvagjhfajafvhzjafqpoieurpguatqohvjafsdjzjvjaflhjqwreoyquqpz', expected_output: '1120' }
                ]
            },
            {
                title: '10.合并字符串',
                description: `## 编程题目

**题目描述：** 编写一个函数 void str_bin(char str1[], char str2[])，str1、str2 是两个有序字符串（其中字符按 ASCII 码从小到大排序），将 str2 合并到字符串 str1 中，要求合并后的字符串仍是有序的，允许字符重复。在 main 函数中测试该函数：从键盘输入两个有序字符串，然后调用该函数，最后输出合并后的结果。

**输入形式：** 分行从键盘输入两个有序字符串（不超过 100 个字符）。

**输出形式：** 输出合并后的有序字符串。

**输入样例：**
\`\`\`
aceg
bdfh
\`\`\`

**输出样例：**
\`\`\`
abcdefgh
\`\`\`

**样例说明：** 输入两个有序字符串 aceg 和 bdfh，输出合并后的有序字符串 abcdefgh。

**评分标准：** 结果完全正确得 20 分，每个测试点 4 分，提交程序文件名为 combine.c。`,
                testCases: [
                    { input: 'abcd\nefgh', expected_output: 'abcdefgh' },
                    { input: 'aaaaa\nbbbb', expected_output: 'aaaaabbbb' },
                    { input: 'abbccd\nbc', expected_output: 'abbbcccd' },
                    { input: 'abcde\naf', expected_output: 'aabcdef' },
                    { input: 'aceg\nbdfh', expected_output: 'abcdefgh' }
                ]
            },
            {
                title: '11.连续正整数的和',
                description: `## 编程题目

**题目描述：** 对于一个正整数 x（3<=x<=1000），寻找一种方案，将 x 分解成连续正整数的和。即 x=x1+x2+......+xn，其中 x1、x2、......、xn 是自小至大的连续正整数，且 n>1。比如，对于输入的数字 10，可以分解成：10=1+2+3+4。如果存在多于一种的可行方案，则选取等式右边项的个数最多的那一种。比如，9 可以分解为：9=2+3+4，也可以分解为：9=4+5。但是前一种分解成 3 个数的和，后一种分解成 2 个数的和，所以前一种是有效解。如果无法分解，则输出 No Answer。

**样例输入 1：**
\`\`\`
38
\`\`\`

**样例输出 1：**
\`\`\`
38=8+9+10+11
\`\`\`

**样例输入 2：**
\`\`\`
256
\`\`\`

**样例输出 2：**
\`\`\`
No Answer
\`\`\`

**评分标准：** 结果完全正确得满分，每个测试点 4 分，提交程序文件名为 c0304.c。`,
                testCases: [
                    { input: '9', expected_output: '9=2+3+4' },
                    { input: '38', expected_output: '38=8+9+10+11' },
                    { input: '250', expected_output: '250=3+4+5+6+7+8+9+10+11+12+13+14+15+16+17+18+19+20+21+22' },
                    { input: '255', expected_output: '255=7+8+9+10+11+12+13+14+15+16+17+18+19+20+21+22+23' },
                    { input: '256', expected_output: 'No Answer' }
                ]
            },
            {
                title: '12.合数分解',
                description: `## 编程题目

**题目描述：** 由数学基本定理可知：任何一个大于 1 的非素数整数（即合数）都可以唯一分解成若干个素数的乘积。编写程序，从控制台读入一个合数（合数的大小不会超过 int 数据类型表示的范围），求这个合数可以分解成的素数。

**输入形式：** 从控制台输入一个合数。

**输出形式：** 在标准输出上按照由小到大的顺序输出分解成的素数，各素数之间以一个空格分隔，最后一个整数后也可以有一个空格。

**输入样例：**
\`\`\`
12308760
\`\`\`

**输出样例：**
\`\`\`
2 2 2 3 3 3 3 5 29 131
\`\`\`

**样例说明：** 输入的合数为 12308760，其分解成的素数乘积为：2×2×2×3×3×3×3×5×29×131。

**评分标准：** 该题要求输出合数分解成的素数，共有 5 个测试点，提交程序文件名为 primes.c。`,
                testCases: [
                    { input: '4', expected_output: '2 2 ' },
                    { input: '12', expected_output: '2 2 3 ' },
                    { input: '3456650', expected_output: '2 5 5 257 269 ' },
                    { input: '59049', expected_output: '3 3 3 3 3 3 3 3 3 3 ' },
                    { input: '323', expected_output: '17 19 ' }
                ]
            },
            {
                title: '13.计算公式：求π的值',
                description: `## 编程题目

**题目描述：** 给定一个精度值 e，用下列公式计算 π 的近似值，要求前后两次 π 的迭代之差的绝对值小于 e，给出相应的最小迭代次数 n 和最后一次计算的 π 的值。

π/2 = 1 + 1!/3 + 2!/(3×5) + 3!/(3×5×7) + … + (n-1)!/(3×5×7×…×(2n-1))

**输入形式：** 从控制台输入 e（e>=0.000001）的值。

**输出形式：** 输出迭代次数 n 和最后一次计算的 π 的值（以一个空格分隔，并且输出 π 时要求小数点后保留 7 位有效数字）。

**样例输入：**
\`\`\`
0.000003
\`\`\`

**样例输出：**
\`\`\`
19 3.1415912
\`\`\`

**样例说明：** 输入的精度 e 为 0.000003，当 n 为 17 时，计算的 π 值为 3.1415864，n 为 18 时计算的 π 值为 3.1415896，两者之差为 0.0000032，大于给定的精度值，所以需要继续计算。当 n 为 19 时，计算的 π 值为 3.1415912，与上次之差为 0.0000016，小于给定的精度值，所以最小迭代次数为 19，输出的 π 值为 3.1415912。

**注意：**
(1) 为保证计算精度，请使用 double 数据类型保存计算数据。
(2) 应至少迭代两次，即：n>=2。

**评分标准：** 该题要求输出最小迭代次数和 π 的值，共有 5 个测试点。上传 C 语言文件名为 example1a.c。`,
                testCases: [
                    { input: '0.000003', expected_output: '19 3.1415912' },
                    { input: '1', expected_output: '2 2.6666667' },
                    { input: '0.001', expected_output: '11 3.1411060' },
                    { input: '0.000001', expected_output: '20 3.1415919' },
                    { input: '0.00008', expected_output: '14 3.1415380' }
                ]
            },
            {
                title: '14.文件排版（非文件）',
                description: `## 编程题目

**题目描述：** 英文电影中参演人员名单一般以某种方式进行排版显示。从控制台输入未排版的内容，该内容中每行参演人员名单由冒号":"分隔成前后两部分，但格式杂乱无章，单词（由除空格和水平制表符之外的其它字符构成）之间可能有多个空格或水平制表符分隔。编写程序，要求将其按如下排版规则排版输出：

- 先从标准输入读取一整数，作为排版后所有各行冒号":"在一行中的固定位置；假设输入的整数肯定大于排版后所有各行冒号":"前的字符个数，位置从 1 开始计数；
- 冒号":"左边的单词串以冒号为基准右对齐，左边的第一个单词之前如果有多余的位置，则以空格填充；
- 冒号":"右边的单词串以冒号":"为基准左对齐，最后一个单词后只有回车换行符，不再有其它字符；
- 冒号":"左右两边的单词间都只有一个空格分隔，并且要求冒号两边各有一个空格与单词分隔。

假设输入内容中每行字符个数不超过 100。

**输入形式：** 先从标准输入读入表示冒号":"位置的整数，然后从下一行开始输入待排版的参演人员名单。输入最后，在新的一行开头输入 ctrl+z 结束输入。

**输出形式：** 排版后的参演人员名单输出到标准输出，最后一行之后要输出一个回车换行符。

**评分标准：** 该题要求按照排版规则对内容进行排版，提交程序文件名为 typeset.c。`,
                testCases: [
                    { input: '40\nSupervising    Digital \tColorist\t\t\t:\t\tSteven J. Scott\n   Second\t\tColorist :Andrew Francis\n Digital Intermediate Producer:Loan \tPhan\nDigital \t  Intermediate Editor:  Devon \tMiller    \t', expected_output: '          Supervising Digital Colorist : Steven J. Scott\n                        Second Colorist : Andrew Francis\n          Digital Intermediate Producer : Loan Phan\n            Digital Intermediate Editor : Devon Miller' },
                    { input: '25\nTemp Music Editor:\tRICHARD FORD', expected_output: '      Temp Music Editor : RICHARD FORD' },
                    { input: '30\nTemp Music Editor : RICHARD FORD\nScore Producer : JAKE MONACO\nMusic Recorded and Mixed by : CASEY STONE\nScore Recorded by : STEVE KAPLAN', expected_output: '           Temp Music Editor : RICHARD FORD\n               Score Producer : JAKE MONACO\n  Music Recorded and Mixed by : CASEY STONE\n            Score Recorded by : STEVE KAPLAN' },
                    { input: '41\nDigital Intermediate Assistant Producer\t:\tPHILIPPE MAJDALANI\nDigital Opticals:\t\tGUS DORAN\nColor Timer:CHRIS REGAN\nAdditional Digital Opticals by\t:\tCIS HOLLYWOOD\nDolby Consultant:THOMAS "COACH" EHLE', expected_output: 'Digital Intermediate Assistant Producer : PHILIPPE MAJDALANI\n                        Digital Opticals : GUS DORAN\n                             Color Timer : CHRIS REGAN\n          Additional Digital Opticals by : CIS HOLLYWOOD\n                        Dolby Consultant : THOMAS "COACH" EHLE' },
                    { input: '50\n\t\tDigital    Intermediate \t\tby:EFILM    \n\t\t Supervising  \t   Digital \t Colorist \t: \tSTEVEN J. SCOTT\nSecond\t\tColorist : \t\t\t\t\tANDREW FRANCIS\n     Digital Intermediate Producer:LOAN PHAN\n\t\tDigital Intermediate Editor:DEVON MILLER\n\t   \tDigital Intermediate Assistant Producer\t:\tPHILIPPE MAJDALANI\nDigital Opticals:\t\tGUS DORAN\nColor Timer:CHRIS REGAN\n  \tAdditional Digital Opticals by\t:\tCIS HOLLYWOOD\nDolby Consultant:THOMAS "COACH" EHLE\nAdditional Music by:\tMARK KILIAN\n \tMusic Editor:\tJENNIFER NASH\nAdditional Music Editor:\tLISE RICHARDSON\nTemp Music \tEditor:\t\t\t\t\tRICHARD FORD\n  \tScore Producer:\tJAKE MONACO\nMusic Recorded and Mixed by:\tCASEY STONE\nScore Recorded by :STEVE KAPLAN', expected_output: '                         Digital Intermediate by : EFILM\n                     Supervising Digital Colorist : STEVEN J. SCOTT\n                                  Second Colorist : ANDREW FRANCIS\n                    Digital Intermediate Producer : LOAN PHAN\n                      Digital Intermediate Editor : DEVON MILLER\n          Digital Intermediate Assistant Producer : PHILIPPE MAJDALANI\n                                 Digital Opticals : GUS DORAN\n                                      Color Timer : CHRIS REGAN\n                   Additional Digital Opticals by : CIS HOLLYWOOD\n                                 Dolby Consultant : THOMAS "COACH" EHLE\n                              Additional Music by : MARK KILIAN\n                                     Music Editor : JENNIFER NASH\n                          Additional Music Editor : LISE RICHARDSON\n                                Temp Music Editor : RICHARD FORD\n                                   Score Producer : JAKE MONACO\n                      Music Recorded and Mixed by : CASEY STONE\n                                Score Recorded by : STEVE KAPLAN' }
                ]
            },
            {
                title: '15.注释比例',
                description: `## 编程题目

**题目描述：** 一个好的程序要有一定比例的注释。编写一个程序统计一个 C 源文件中注释所占的百分比。百分比计算公式为：程序注释中字符总数（/\* 和 \*/ 除外的所有字符）除以程序文件中总字符数（程序文件中的所有字符）。

注：只简单考虑 /\*…\*/ 的注释，而且要考虑注释跨行的情况，不要考虑其它复杂情况。

**输入形式：** 从当前目录下的 filein.c 源程序文件获得输入。

**输出形式：** 向控制台输出注释所占百分比，百分数无小数（小数部分直接截掉，不要四舍五入），后跟百分号 %。

**样例说明：** filein.c 文件的总字符数为 179，注释中的字符数为 41，则注释所占百分比为 22%。

**评分标准：** 该题要求输出注释所占百分比，共有 5 个测试点。上传 C 语言文件名为 comment.c。

**注意：** 本题需要使用文件操作（读取 filein.c）。`,
                ioMode: 'file',
                inputFile: 'filein.c',
                testCases: [
                    { input: 'void main()\n{\n\tFILE * in;\n\t/*Open the file*/\n\tin=fopen("in.txt","r");\n\tfclose(in);\n}', expected_output: '15%' },
                    { input: "void main()\n{\n\tFILE * in;\n\t/*Open the file,\n\tif error then return.*/\n\tif((in=fopen(\"in.txt\",\"r\"))==NULL)\n\t{\n\t\tprintf(\"Can't open in.txt!\");\n\t\treturn;\n\t}\n\t/*Close the file,\n\tand return.*/\n\tfclose(in);\n}", expected_output: '32%' },
                    { input: "void main()\n{\nFILE * in;\n/*Open the file*/if((in=fopen(\"in.txt\",\"r\"))==NULL)\n{\n\tprintf(\"Can't open in.txt!\");\n\treturn;\n}\nfclose(in);/*Close the file*/\n}", expected_output: '17%' },
                    { input: "void main()\n{\n\tFILE * in;\n\t/**/\n\tif((in=fopen(\"in.txt\",\"r\"))==NULL)\n\t{\n\t\tprintf(\"Can't open in.txt!\");\n\t\treturn;\n\t}\n\tfclose(in);/**/\n}", expected_output: '0%' },
                    { input: "void main()\n{\n\tFILE * in;\n\tif((in=fopen(\"in.txt\",\"r\"))==NULL)\n\t{\n\t\tprintf(\"Can't open in.txt!\");\n\t\treturn;\n\t}\n\tfclose(in);\n}", expected_output: '0%' }
                ]
            },
            {
                title: '16.删除子串',
                description: `## 编程题目

**题目描述：** 编写一个程序，当在一个字符串中出现子串时就删除它。

**输入形式：** 用户在第一行输入一个字符串，用户在第二行输入一个子串。

**输出形式：** 程序在下一行输出删除其中所有子串后的字符串。如果字符串不包含子串则输出原字符串本身。

**样例输入：**
\`\`\`
I am a boy!
a
\`\`\`

**样例输出：**
\`\`\`
I m  boy!
\`\`\`

**样例说明：** 用户首先输入字符串 I am a boy!，然后输入子串 a，程序会寻找字符串中的子串删除它，最后将删除后的结果输出。

**评分标准：** 结果完全正确得 20 分，每个测试点 4 分。提交程序名为：delsubstring.c。`,
                testCases: [
                    { input: 'Today is Sunday!\nis', expected_output: 'Today  Sunday!' },
                    { input: 'Ah Love!could you and I with Fate conspire\nould', expected_output: 'Ah Love!c you and I with Fate conspire' },
                    { input: 'amethystic is a girl.\n ', expected_output: 'amethysticisagirl.' },
                    { input: '4+6=10\n+', expected_output: '46=10' },
                    { input: 'aabbaa\naa', expected_output: 'bb' }
                ]
            }
        ]
    },
    'homework1':{
        name: '25级第一次作业',
        problems: [
            {
                title: '1.字母频率统计',
                description: `## 编程题目

**问题描述：**

编写程序从标准输入中读入一段英文，统计其中小写字母出现次数，并以柱状图的形式显示其出现次数。

**输入形式：**

在标准输入上输入一段英文文章（可能有一行，也可能有多行），在新的一行的开头输入ctrl+z键表示结束。

**输出形式：**

在屏幕上依次输出表示每个小写字母出现次数的柱状图（以“*”字符表示柱状图，空白处用空格字符表示，某个小写字母出现多少次，就显示多少“*”字符；柱状图的高度以出现最多的字母次数为准），在最后一行依次输出26个小写字母。

**样例输入：**
\`\`\`
The computing world has undergone a
revolution since the publication of
The C Programming Language in 1978.
\`\`\`

**样例输出：**

![image-20260302174235450](/static/images/1_1.png)

**样例说明：**

在输入的英文短文中，小写字母a出现了6次，所以其上输出了6个字符"*"。出现次数最多的是字母n，所以柱状图的高度为9个字符。字母j没有出现，所以其上都为空格字符。

**评分标准：**

该题要求输出柱状图表示的字母出现次数，共有5个测试点。上传C语言文件名为bar.c。`,
                testCases: [
                    { input: 'The computing world', expected_output: '              *           \n  *** ***  ***** * ** *   \nabcdefghijklmnopqrstuvwxyz' },
                    { input: 'THE WORLD', expected_output: 'abcdefghijklmnopqrstuvwxyz' },
                    { input: 'az', expected_output: '*                        *\nabcdefghijklmnopqrstuvwxyz' },
                    { input: 'Big computers are much bigger,\nand personal computers \nhave capabilities that', expected_output: '*   *                     \n*   *                     \n*   *   *        * *      \n* * *   *      * ***      \n* * * ***   * ** ****     \n*** * ***  ***** ****     \n***** ***  ***** *****    \nabcdefghijklmnopqrstuvwxyz' },
                    { input: 'zzzzzzzzzz\nzzzzzzzzzz', expected_output: '                         *\n                         *\n                         *\n                         *\n                         *\n                         *\n                         *\n                         *\n                         *\n                         *\n                         *\n                         *\n                         *\n                         *\n                         *\n                         *\n                         *\n                         *\n                         *\n                         *\nabcdefghijklmnopqrstuvwxyz' }
                ]
            },
            {
                title: '2.扩展字符A',
                description: `## 编程题目

**问题描述：**
从键盘输入包含扩展符'-'的字符串，将其扩展为等价的完整字符，例如将a-d扩展为abcd，并输出扩展后的字符串。

要求：只处理[a-z]、[A-Z]、[0-9]范围内的字符扩展，即只有当扩展符前后的字符同时是小写字母、大写字母或数字，并且扩展符后的字符大于扩展符前的字符时才进行扩展，其它情况不进行扩展，原样输出。例如：a-R、D-e、0-b、4-B等字符串都不进行扩展。


**输入形式：**
从键盘输入包含扩展符的字符串

**输出形式：**
输出扩展后的字符串

**输入样例1：**
\`\`\`
ADEa-g-m02
\`\`\`
**输出样例1：**
\`\`\`
ADEabcdefghijklm02
\`\`\`

**输入样例2：**
\`\`\`
cdeT-bcd
\`\`\`
**输出样例2：**
\`\`\`
cdeT-bcd
\`\`\`

**样例说明：**
将样例1的输入ADEa-g-m02扩展为：ADEabcdefghijklm02；样例2的输入cdeT-bcd中，扩展符前的字符为大写字母，扩展符后的字符为小写字母，不在同一范围内，所以不进行扩展。

**评分标准：**
该题要求扩展字符，提交程序文件expand.c。`,
                testCases: [
                    { input: 'a-uB-F', expected_output: 'abcdefghijklmnopqrstuBCDEF' },
                    { input: 'dcu0-8', expected_output: 'dcu012345678' },
                    { input: 'B-e', expected_output: 'B-e' },
                    { input: 'toooold08A-a', expected_output: 'toooold08A-a' },
                    { input: 'a-c-g0-A', expected_output: 'abcdefg0-A' }
                ]
            },
            {
                title: '3.表达式计算（支持空格，连乘，连除）',
                description: `## 编程题目

**问题描述：**

从标准输入中读入一个整数算术运算表达式，如5 - 1 * 2 * 3 + 12 / 2 / 2  = 。计算表达式结果，并输出。

要求：
1、表达式运算符只有+、-、*、/，表达式末尾的&rsquo;=&rsquo;字符表示表达式输入结束，表达式中可能会出现空格；
2、表达式中不含圆括号，不会出现错误的表达式；
3、出现除号/时，以整数相除进行运算，结果仍为整数，例如：5/3结果应为1。

**输入形式：**

在控制台中输入一个以&rsquo;=&rsquo;结尾的整数算术运算表达式。

**输出形式：**

向控制台输出计算结果（为整数）。

**样例1输入：**
\`\`\`
5 - 1 * 2 * 3 + 12 / 2 / 2  =
\`\`\`
**样例1输出：**
\`\`\`
2
\`\`\`
**样例2输入：**
\`\`\`
500 =
\`\`\`
**样例2输出：**
\`\`\`
500
\`\`\`

**样例1说明：**

输入的表达式为5 - 1 * 2 * 3 + 12 / 2 / 2 =，按照整数运算规则，计算结果为2，故输出2。

**样例2说明：**

输入的表达式为500 = ，没有运算符参与运算，故直接输出500。

算法之一提示：
1、可以利用gets函数，读取整行表达式；
2、对于空格，可以考虑首先去除表达式中的所有空格
3、可以设一计数器用来记录已读取、但未参加运算的运算符的个数，根据该计数器来判断如何进行运算；
4、可以设计一函数：实现二元整数算术运算。

**评分标准：**

该题要求输出整数表达式的计算结果，共有5个测试点。上传C语言文件名为example1c.c。

 `,
                testCases: [
                    { input: '10 + 20 * 30 - 40 / 5 =', expected_output: '602' },
                    { input: '24 / 4 / 3 / 2 * 2 * 3 * 4 =', expected_output: '24' },
                    { input: '24 / 4 / 3 / 2 + 100 - 50 - 40 + 10*20*30*40 / 40 / 30 =', expected_output: '211' },
                    { input: '100 *    200  *   0 *300*400*500+500/600+12000=', expected_output: '12000' },
                    { input: '   0  =', expected_output: '0' }
                ]
            },
            {
                title: '4.小数形式与科学计数法转换（简）',
                description: `## 编程题目
                
**问题描述：**

编写一个程序，将用小数表示的浮点数，转换成科学计数法的形式输出。输入的数据没有符号，小数点前后必有数字，且全为有效数据，即小数点后的末尾数字不为0；小数点前若只有一位数字，可以为0，否则小数点前的最高位数字不为0。

提示：以字符串形式保存相关数据。

**输入形式：**

从控制台输入一小数，最后有回车换行符，所有输入的字符数不会超过100。

**输出形式：**

以科学计数法形式输出数据。输出的数据由以下几部分构成：
1.底数部分是一个小数或整数，若为小数，则小数点前后必有数字，而且都为有效数字。即：小数点前只有一位大于0的数字，小数点后的末尾数字不能为0。若为整数，则只有一位数字，不带小数点。
2.必有小写字母“e”。
3.指数部分是一个整数，若大于等于0，则不带正号“+”。若小于0，则需要带负号“-”，且整数的最高位数字不为0。

**输入样例1：**
\`\`\`
0.000000000000002
\`\`\`
**输出样例1：**
\`\`\`
2e-15
\`\`\`

**输入样例2：**
\`\`\`
8.9845623489651700659
\`\`\`
**输出样例2：**
\`\`\`
8.9845623489651700659e0
\`\`\`

**输入样例3：**
\`\`\`
367298599999093453490394859509568659795603.4
\`\`\`
**输出样例3：**
\`\`\`
3.672985999990934534903948595095686597956034e41
\`\`\`

**样例说明：**

以小数形式输入数据，然后转换成科学计数法形式输出。

**评分标准：**

该题要求以科学计数法形式输出数据，提交程序文件名为notation.c。
 `,
                testCases: [
                    { input: '0.9', expected_output: '9e-1' },
                    { input: '0.00000009123456789012', expected_output: '9.123456789012e-8' },
                    { input: '87899.9999999999000999', expected_output: '8.78999999999999000999e4' },
                    { input: '5123456789012345678909934958349058395854956984596456893495439.1', expected_output: '5.1234567890123456789099349583490583958549569845964568934954391e60' },
                    { input: '9.99', expected_output: '9.99e0' }
                ]
            },
            {
                title: '5.超长正整数的减法',
                description: `## 编程题目
                
**问题描述：**
编写程序实现两个超长正整数（每个最长80位数字）的减法运算。
 
**输入形式：**

从键盘读入两个整数，要考虑输入高位可能为0的情况（如00083）。
1. 第一行是超长正整数A；
2. 第二行是超长正整数B；
 
**输出形式：**
输出只有一行，是长整数A减去长整数B的运算结果，从高到低依次输出各位数字。要求：若结果为0，则只输出一个0；否则输出的结果的最高位不能为0，并且各位数字紧密输出。

 **输入样例：**
 \`\`\`
234098
134098703578230056
\`\`\`
 **输出样例：**
 \`\`\`
 －134098703577995958
\`\`\`

**样例说明：**
进行两个正整数减法运算， 234098 －134098703578230056 = －134098703577995958。
 
**评分标准：**
 完全正确得20分，每个测试点4分，提交程序文件名为subtract.c。
`,
                testCases: [
                    { input: '234098\n134098703578230056', expected_output: '-134098703577995958' },
                    { input: '989764327215344864926494623968964296\n67598643895984573429347848936584', expected_output: '989696728571448880353065276120027712' },
                    { input: '000000000000000000076616616263663772\n000000000000000000076616616263663778', expected_output: '-6' },
                    { input: '1\n10000000000000000000000000', expected_output: '-9999999999999999999999999' },
                    { input: '99999999999999999999999999999999999999999999999999999999999999999999999999999997\n99999999999999999999999999999999999999999999999999999999999999999999999999999997', expected_output: '0' }
                ]
            },
            {
                title: '6.全排列数的生成',
                description: `## 编程题目
                
**问题描述：**
输入整数N( 1 <= N <= 10 )，生成从1-N所有整数的全排列。

**输入形式：**
输入整数N。

**输出形式：**
输出有N!行，每行都是从1~N所有整数的一个全排列，各整数之间以空格分隔。各行上的全排列不重复。输出各行遵循“小数优先”原则, 在各全排列中，较小的数尽量靠前输出。如果将每行上的输出看成一个数字，则所有输出构成升序数列。具体格式见输出样例。

**样例输入1：**
\`\`\`
1
\`\`\`
**样例输出1：**
\`\`\`
1
\`\`\`
**样例说明1：**输入整数N=1，其全排列只有一种。
**样例输入2：**
\`\`\`
3 
\`\`\`
**样例输出2：**
\`\`\`
1 2 3
1 3 2
2 1 3
2 3 1
3 1 2
3 2 1
\`\`\`
**样例说明2：**
输入整数N=3，要求整数1、2、3的所有全排列, 共有N!=6行。且先输出1开头的所有排列数，再输出2开头的所有排列数，最后输出3开头的所有排列数。在以1开头的所有全排列中同样遵循此原则。

**样例输入3：**
\`\`\`
10
\`\`\`
**样例输出3：**
\`\`\`
1 2 3 4 5 6 7 8 9 10
1 2 3 4 5 6 7 8 10 9
1 2 3 4 5 6 7 9 8 10
1 2 3 4 5 6 7 9 10 8
1 2 3 4 5 6 7 10 8 9
1 2 3 4 5 6 7 10 9 8
1 2 3 4 5 6 8 7 9 10
1 2 3 4 5 6 8 7 10 9
1 2 3 4 5 6 8 9 7 10
1 2 3 4 5 6 8 9 10 7
&hellip;&hellip;&hellip;&hellip;&hellip;&hellip;&hellip;&hellip;
\`\`\`
**样例说明3：**
输入整数N=10，要求整数1、2、3、&hellip;&hellip;、10的所有全排列。上例显示了输出的前10行。

**运行时限：**
要求每次运行时间限制在20秒之内。超出该时间则认为程序错误。提示：当N增大时，运行时间将急剧增加。在编程时要注意尽量优化算法，提高运行效率。

**评分标准：**
该题要求输出若干行整数。。`,
                testCases: [
                    { input: '1', expected_output: '1' },
                    { input: '2', expected_output: '1 2 \n2 1 ' },
                    { input: '3', expected_output: '1 2 3 \n1 3 2 \n2 1 3 \n2 3 1 \n3 1 2 \n3 2 1 ' },
                    { input: '4', expected_output: '1 2 3 4 \n1 2 4 3 \n1 3 2 4 \n1 3 4 2 \n1 4 2 3 \n1 4 3 2 \n2 1 3 4 \n2 1 4 3 \n2 3 1 4 \n2 3 4 1 \n2 4 1 3 \n2 4 3 1 \n3 1 2 4 \n3 1 4 2 \n3 2 1 4 \n3 2 4 1 \n3 4 1 2 \n3 4 2 1 \n4 1 2 3 \n4 1 3 2 \n4 2 1 3 \n4 2 3 1 \n4 3 1 2 \n4 3 2 1 ' },
                    { input: '5', expected_output: '1 2 3 4 5 \n1 2 3 5 4 \n1 2 4 3 5 \n1 2 4 5 3 \n1 2 5 3 4 \n1 2 5 4 3 \n1 3 2 4 5 \n1 3 2 5 4 \n1 3 4 2 5 \n1 3 4 5 2 \n1 3 5 2 4 \n1 3 5 4 2 \n1 4 2 3 5 \n1 4 2 5 3 \n1 4 3 2 5 \n1 4 3 5 2 \n1 4 5 2 3 \n1 4 5 3 2 \n1 5 2 3 4 \n1 5 2 4 3 \n1 5 3 2 4 \n1 5 3 4 2 \n1 5 4 2 3 \n1 5 4 3 2 \n2 1 3 4 5 \n2 1 3 5 4 \n2 1 4 3 5 \n2 1 4 5 3 \n2 1 5 3 4 \n2 1 5 4 3 \n2 3 1 4 5 \n2 3 1 5 4 \n2 3 4 1 5 \n2 3 4 5 1 \n2 3 5 1 4 \n2 3 5 4 1 \n2 4 1 3 5 \n2 4 1 5 3 \n2 4 3 1 5 \n2 4 3 5 1 \n2 4 5 1 3 \n2 4 5 3 1 \n2 5 1 3 4 \n2 5 1 4 3 \n2 5 3 1 4 \n2 5 3 4 1 \n2 5 4 1 3 \n2 5 4 3 1 \n3 1 2 4 5 \n3 1 2 5 4 \n3 1 4 2 5 \n3 1 4 5 2 \n3 1 5 2 4 \n3 1 5 4 2 \n3 2 1 4 5 \n3 2 1 5 4 \n3 2 4 1 5 \n3 2 4 5 1 \n3 2 5 1 4 \n3 2 5 4 1 \n3 4 1 2 5 \n3 4 1 5 2 \n3 4 2 1 5 \n3 4 2 5 1 \n3 4 5 1 2 \n3 4 5 2 1 \n3 5 1 2 4 \n3 5 1 4 2 \n3 5 2 1 4 \n3 5 2 4 1 \n3 5 4 1 2 \n3 5 4 2 1 \n4 1 2 3 5 \n4 1 2 5 3 \n4 1 3 2 5 \n4 1 3 5 2 \n4 1 5 2 3 \n4 1 5 3 2 \n4 2 1 3 5 \n4 2 1 5 3 \n4 2 3 1 5 \n4 2 3 5 1 \n4 2 5 1 3 \n4 2 5 3 1 \n4 3 1 2 5 \n4 3 1 5 2 \n4 3 2 1 5 \n4 3 2 5 1 \n4 3 5 1 2 \n4 3 5 2 1 \n4 5 1 2 3 \n4 5 1 3 2 \n4 5 2 1 3 \n4 5 2 3 1 \n4 5 3 1 2 \n4 5 3 2 1 \n5 1 2 3 4 \n5 1 2 4 3 \n5 1 3 2 4 \n5 1 3 4 2 \n5 1 4 2 3 \n5 1 4 3 2 \n5 2 1 3 4 \n5 2 1 4 3 \n5 2 3 1 4 \n5 2 3 4 1 \n5 2 4 1 3 \n5 2 4 3 1 \n5 3 1 2 4 \n5 3 1 4 2 \n5 3 2 1 4 \n5 3 2 4 1 \n5 3 4 1 2 \n5 3 4 2 1 \n5 4 1 2 3 \n5 4 1 3 2 \n5 4 2 1 3 \n5 4 2 3 1 \n5 4 3 1 2 \n5 4 3 2 1 ' }
                ]
            },
        ]
    },
    'homework2':{
        name: '25级第二次作业',
        problems: [
            {
                title: '1.五子棋危险判断',
                description: `## 编程题目

**问题描述**

已知两人分别执白棋和黑棋在一个围棋棋盘上下五子棋，若同一颜色的棋子在同一条横行、纵行或斜线上连成5个棋子，则执该颜色棋子的人获胜。编写程序读入某一时刻下棋的状态，并判断是否有人即将获胜，即：同一颜色的棋子在同一条横行、纵列或斜线上连成4个棋子，且该4个棋子的两端至少有一端为空位置。
输入的棋盘大小是19&times;19，用数字0表示空位置（即没有棋子），用数字1表示该位置下了一白色棋子，用数字2表示该位置下了一黑色棋子。假设同一颜色的棋子在同一条横行、纵列或斜线上连成的棋子个数不会超过4个，并且最多有一人连成线的棋子个数为4。

**输入形式**

从控制台输入用来表示棋盘状态的数字0、1或2；每行输入19个数字，各数字之间以一个空格分隔，每行最后一个数字后没有空格；共输入19行表示棋盘状态的数字。

**输出形式**

若有人即将获胜，则先输出即将获胜人的棋子颜色（1表示白色棋子，2表示黑色棋子），然后输出英文冒号:，最后输出连成4个棋子连线的起始位置（棋盘横行自上往下、纵列自左往右从1开始计数，横行最小的棋子在棋盘上的横行数和纵列数作为连线的起始位置，若在同一行上，则纵列数最小的棋子位置作为起始位置，两数字之间以一个英文逗号,作为分隔符）。
若没有人获胜，则输出英文字符串：No。
无论输出什么结果，最后都要有回车换行符。

**输入样例1**
\`\`\`
0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
0 0 0 0 0 0 0 0 0 0 2 0 0 0 0 0 0 0 0
0 0 0 0 0 0 0 2 0 1 1 2 0 0 0 0 0 0 0
0 0 0 0 0 2 1 1 1 1 2 2 0 0 0 0 0 0 0
0 0 0 0 0 0 0 1 2 1 2 0 0 0 0 0 0 0 0
0 0 0 0 0 0 1 1 0 2 2 0 0 0 0 0 0 0 0
0 0 0 0 0 2 0 1 0 0 2 0 0 0 0 0 0 0 0
0 0 0 0 0 0 0 0 0 0 1 2 0 0 0 0 0 0 0
0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 0 0 0
0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
\`\`\`
**输出样例1**
\`\`\`
1:9,8
\`\`\`
**输入样例2**
\`\`\`
0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
0 0 0 0 0 0 0 1 2 0 0 0 0 0 0 0 0 0 0
0 0 0 0 0 0 0 1 2 2 0 0 0 0 0 0 0 0 0
0 0 0 0 0 0 0 0 1 0 0 0 0 0 0 0 0 0 0
0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
\`\`\`
**输出样例2**
\`\`\`
No
\`\`\`

**样例说明**

在输入的样例1中，执白棋（数字1表示）的人即将获胜，连成4个棋子且有一端为空的起始位置在第9行第8列，所以输出1:9,8。
在输入的样例2中，还没有同一颜色的棋子连成4个，所以无人即将获胜，直接输出No。

**评分标准**

该题要求判断五子棋的棋盘状态，提交程序文件名为chess.c。
 `,
                testCases: [
                    { input: '0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0\n0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0\n0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0\n0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0\n0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0\n0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0\n0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0\n0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0\n0 0 0 0 0 0 0 0 0 0 2 0 0 0 0 0 0 0 0\n0 0 0 0 0 0 0 2 0 1 1 2 0 0 0 0 0 0 0\n0 0 0 0 0 2 1 1 1 1 2 2 0 0 0 0 0 0 0\n0 0 0 0 0 0 0 1 2 1 2 0 0 0 0 0 0 0 0\n0 0 0 0 0 0 1 1 0 2 2 0 0 0 0 0 0 0 0\n0 0 0 0 0 2 0 1 0 0 2 0 0 0 0 0 0 0 0\n0 0 0 0 0 0 0 0 0 0 1 2 0 0 0 0 0 0 0\n0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 0 0 0\n0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0\n0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0\n0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0', expected_output: '1:11,8' },
                    { input: '2 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0\n2 1 2 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0\n2 2 1 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0\n0 2 2 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0\n0 1 1 0 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0\n0 0 2 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0\n0 0 0 2 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0\n0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0\n0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0\n0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0\n0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0\n0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0\n0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0\n0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0\n0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0\n0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0\n0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0\n0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0\n0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0', expected_output: '1:2,2' },
                    { input: '0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0\n0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0\n0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0\n0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0\n0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0\n0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0\n0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0\n0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0\n0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0\n0 0 0 0 0 0 0 0 0 0 1 0 0 0 0 0 0 0 0\n0 0 0 0 0 0 0 0 1 2 0 0 0 0 0 0 0 0 0\n0 0 0 0 0 0 0 1 2 1 0 0 0 0 0 0 0 0 0\n0 0 0 0 0 0 0 2 2 1 0 0 0 0 0 0 0 0 0\n0 0 0 0 0 0 2 0 1 0 0 0 0 0 0 0 0 0 0\n0 0 0 0 0 0 0 0 2 0 0 0 0 0 0 0 0 0 0\n0 0 0 0 0 0 0 0 2 0 0 0 0 0 0 0 0 0 0\n0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0\n0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0\n0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0', expected_output: '2:11,10' },
                    { input: '0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0\n0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0\n0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0\n0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0\n0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0\n0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0\n0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0\n0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0\n0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0\n0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0\n0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0\n0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0\n0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0\n0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1\n0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 2 0\n0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 2 0 0\n0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 2 1 1 1\n0 0 0 0 0 0 0 0 0 0 0 0 0 0 2 2 1 2 0\n0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0', expected_output: '2:15,18' },
                    { input: '0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0\n0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0\n0 0 0 0 0 0 0 0 0 0 2 0 0 0 0 0 0 0 0\n0 0 0 0 0 0 0 0 0 1 0 0 0 0 0 0 0 0 0\n0 0 0 0 0 1 2 0 1 1 1 0 0 0 0 0 0 0 0\n0 0 0 0 0 2 1 1 2 2 1 0 0 0 0 0 0 0 0\n0 0 0 0 0 0 1 1 1 2 2 0 0 0 0 0 0 0 0\n0 0 0 0 0 2 1 0 2 1 1 0 2 0 0 0 0 0 0\n0 0 0 0 0 2 1 2 2 2 2 1 2 0 0 0 0 0 0\n0 0 0 0 0 2 0 0 0 0 2 0 1 0 0 0 0 0 0\n0 0 0 0 0 0 0 0 0 0 2 2 1 2 0 0 0 0 0\n0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 0 0 0\n0 0 0 0 0 0 0 0 0 0 0 0 2 0 0 0 0 0 0\n0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0\n0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0\n0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0\n0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0\n2 2 2 2 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0\n1 1 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0', expected_output: '1:6,7' }
                ]
            },
            {
                title: '2.字符串替换（新）',
                description: `## 编程题目

**问题描述**

编写程序将一个指定文件中某一字符串替换为另一个字符串。要求：（1）被替换字符串若有多个，均要被替换；（2）指定的被替换字符串，大小写无关。

**输入形式**

给定文件名为filein.txt。从控制台输入两行字符串（不含空格，行末尾都有回车换行符），分别表示被替换的字符串和替换字符串。

**输出形式**

将替换后的结果输出到文件fileout.txt中。

**样例输入**

从控制台输入两行字符串：

\`\`\`
in

out
\`\`\`

文件filein.txt的内容为：

\`\`\`
#include <stdio.h>

void main()

{

    FILE * IN;

    if((IN=fopen("in.txt","r"))==NULL)

    {

       printf("Can&rsquo;t open in.txt!");

       return;

    }

    fclose(IN);

}
\`\`\`

**样例输出**

文件fileout.txt的内容应为：

\`\`\`
#outclude <stdio.h>

void maout()

{

    FILE * out;

    if((out=fopen("out.txt","r"))==NULL)

    {

       prouttf("Can&rsquo;t open out.txt!");

       return;

    }

    fclose(out);

}
\`\`\`

**样例说明**

输入的被替换字符串为in，替换字符串为out，即将文件filein.txt中的所有in字符串（包括iN、In、IN字符串）全部替换为out字符串，并输出保存到文件fileout.txt中。

**评分标准**

该题要求得到替换后的文件内容，共有5个测试点。上传C语言文件名为replace.c。`,
                testCases: [
                    { input: 'a-uB-F', expected_output: 'abcdefghijklmnopqrstuBCDEF' },
                    { input: 'dcu0-8', expected_output: 'dcu012345678' },
                    { input: 'B-e', expected_output: 'B-e' },
                    { input: 'toooold08A-a', expected_output: 'toooold08A-a' },
                    { input: 'a-c-g0-A', expected_output: 'abcdefg0-A' }
                ]
            },
            {
                title: '3.加密文件',
                description: `## 编程题目

**问题描述**

有一种加密方法为：其使用一个字母串（可以含重复字母，字母个数不超过50）作为密钥。假定密钥单词串为feather，则先去掉密钥单词中的重复字母得到单词串feathr，然后再将字母表中的其它字母以反序追加到feathr的后面：

 f	 e	 a	 t	 h	 r	 z	 y	 x	 w	 v	 u	 s	 q	 p	 o	 n	 m	 l	 k	 j	 i	 g	 d	 c	 b 
加密字母的对应关系如下：
\`\`\`
 a	 b	 c	 d	 e	 f	 g	 h	 i	 j	 k	 l	 m	 n	 o	 p	 q	 r	 s	 t	 u	 v	 w	 x	 y	 z
 f	 e	 a	 t	 h	 r	 z	 y	 x	 w	 v	 u	 s	 q	 p	 o	 n	 m	 l	 k	 j	 i	 g	 d	 c	 b
\`\`\`
其中第一行为原始英文字母，第二行为对应加密字母。其它字符不进行加密。编写一个程序，用这种密码加密文件。假定要加密的文件名为encrypt.txt及加密后的文件名为output.txt，并假定输入文件中字母全为小写字母，并且输入密钥也全为小写字母。

**输入形式**

从标准输入中输入密钥串，并从文件encrypt.txt中读入要加密的内容。

**输出形式**

加密后结果输出到文件output.txt中。

**样例输入**

\`\`\`
feather
和文件encrypt.txt中内容，例如被加密的文件encrypt.txt中内容为：
c language is wonderful.
\`\`\`

**样例输出**

加密后output.txt文件中内容为：
\`\`\`
a ufqzjfzh xl gpqthmrju.
\`\`\`

**样例说明**

首先将给定的密钥单词去除重复字母，然后按照上面的加密对应表对encrypt.txt文件内容进行加密即可得到加密后的文件，其中只对英文字母进行加密对换，并且假设encrypt.txt中的英文字母全是小写字母。

**评分标准**

该题要求对文件进行加密，共有5个测试点。提交程序名为encrypt.c

 `,
                testCases: [
                    {
                        input: 'kinggnik',
                        files: { 'encrypt.txt': 'k' },
                        expected_files: { 'output.txt': 't' }
                    },
                    {
                        input: 'huxihxhxu',
                        files: { 'encrypt.txt': 'ilovechina' },
                        expected_files: { 'output.txt': 'tqnezxvtoh' }
                    },
                    {
                        input: 'mochamm',
                        files: { 'encrypt.txt': 'huxi is a pretty boy.' },
                        expected_files: { 'output.txt': 'xiew wk m plajjd oqd.' }
                    },
                    {
                        input: 'armymya',
                        files: { 'encrypt.txt': 'windows or linux,which is better?' },
                        expected_files: { 'output.txt': 'euoynei nj quogd,evumv ui rzhhzj?' }
                    },
                    {
                        input: 'callalala',
                        files: { 'encrypt.txt': '2+3=5' },
                        expected_files: { 'output.txt': '2+3=5' }
                    }
                ]
            },
            {
                title: '4.通讯录整理',
                description: `## 编程题目
                
**问题描述**

读取一组电话号码簿（由姓名和手机号码组成），将重复出现的项删除（姓名和电话号码都相同的项为重复项，只保留第一次出现的项），并对姓名相同手机号码不同的项进行如下整理：首次出现的项不作处理，第一次重复的姓名后面加英文下划线字符_和数字1，第二次重复的姓名后面加英文下划线字符_和数字2，依次类推。号码簿中姓名相同的项数最多不超过10个。最后对整理后的电话号码簿按照姓名进行从小到大排序，并输出排序后的电话号码簿。

**输入形式**

先从标准输入读取电话号码个数，然后分行输入姓名和电话号码，姓名由不超过20个英文小写字母组成，电话号码由11位数字字符组成，姓名和电话号码之间以一个空格分隔，输入的姓名和电话号码项不超过100个。

**输出形式**

按照姓名从小到大的顺序分行输出最终的排序结果，先输出姓名再输出电话号码，以一个空格分隔。

**样例输入**
\`\`\`

15

liping 13512345678

zhaohong 13838929457

qiansan 13900223399

zhouhao 18578294857

anhai 13573948758

liping 13512345678

zhaohong 13588339922

liping 13833220099

boliang 15033778877

zhaohong 13838922222

tianyang 18987283746

sunnan 13599882764

zhaohong 13099228475

liushifeng 13874763899

caibiao 13923567890

\`\`\`

**样例输出**
\`\`\`
anhai 13573948758

boliang 15033778877

caibiao 13923567890

liping 13512345678

liping_1 13833220099

liushifeng 13874763899

qiansan 13900223399

sunnan 13599882764

tianyang 18987283746

zhaohong 13838929457

zhaohong_1 13588339922

zhaohong_2 13838922222

zhaohong_3 13099228475

zhouhao 18578294857
\`\`\`

**样例说明**

输入了15个人名和电话号码。其中第一项和第六项完全相同，都是“liping 13512345678”，将第六项删除，第一项保留；

第八项和第一项人名相同，电话不同，则将第八项的人名整理为liping_1；同样，第二项、第七项、第十项、第十三项的人名都相同，将后面三项的人名分别整理为：zhaohong_1、zhaohong_2和zhaohong_3。

最后将整理后的电话簿按照姓名进行从小到大排序，分行输出排序结果。

**评分标准**

该题要求编程实现通讯录的整理与排序，提交程序文件名为sort.c。
 `,
                testCases: [
                    { input: '6\ntianhong 13599887766\npengfei 13866338822\nhuangqi 13976543256\nlengtianyi 18922987658\nwanggong 15033890198\nwanggong 15033890198', expected_output: 'huangqi 13976543256\nlengtianyi 18922987658\npengfei 13866338822\ntianhong 13599887766\nwanggong 15033890198' },
                    { input: '10\nzengshi 18976890198\nzhouhong 13978967835\nzhouhang 13978901236\nzhouhai 13587689012\nliuping 13589076535\ntianliang 13565890126\nzengshi 18976890198\nzhouhang 13578901238\nzhouhang 13858697089\nzhouhai 13687689012', expected_output: 'liuping 13589076535\ntianliang 13565890126\nzengshi 18976890198\nzhouhai 13587689012\nzhouhai_1 13687689012\nzhouhang 13978901236\nzhouhang_1 13578901238\nzhouhang_2 13858697089\nzhouhong 13978967835' },
                    { input: '27\npengfei 13356789098\nwangping 13823890198\nliulaifeng 13589090989\ntianliang 13876567890\nanshifeng 13098789865\npengfei 13356789023\nzengshi 13898765321\nzhouliang 13590890767\nlili 13856789098\npengfei 13856781298\nsunniu 13523675678\nboyitian 13098765678\ntianliang 13876567890\nbaijuyi 13967890976\npengfei 13926789098\nzhangli 13387678909\ntianliang 13876567890\nhaolaiwen 13856127865\npengfei 13823890999\ntianliang 13876567890\nqiandelai 13398760987\npengfei 13588888888\nmaomao 18967890765\npengfei 13922229876\nbaijuyi 13855890976\nbaijuyi 13322890976\nbaijuyi 13511890976', expected_output: 'anshifeng 13098789865\nbaijuyi 13967890976\nbaijuyi_1 13855890976\nbaijuyi_2 13322890976\nbaijuyi_3 13511890976\nboyitian 13098765678\nhaolaiwen 13856127865\nlili 13856789098\nliulaifeng 13589090989\nmaomao 18967890765\npengfei 13356789098\npengfei_1 13356789023\npengfei_2 13856781298\npengfei_3 13926789098\npengfei_4 13823890999\npengfei_5 13588888888\npengfei_6 13922229876\nqiandelai 13398760987\nsunniu 13523675678\ntianliang 13876567890\nwangping 13823890198\nzengshi 13898765321\nzhangli 13387678909\nzhouliang 13590890767' },
                    { input: '10\npengfei 13356789098\npengfei 13356789097\npengfei 13356789096\npengfei 13356789095\npengfei 13356789094\npengfei 13356789093\npengfei 13356789092\npengfei 13356789091\npengfei 13356789090\npengfei 13356789099', expected_output: 'pengfei 13356789098\npengfei_1 13356789097\npengfei_2 13356789096\npengfei_3 13356789095\npengfei_4 13356789094\npengfei_5 13356789093\npengfei_6 13356789092\npengfei_7 13356789091\npengfei_8 13356789090\npengfei_9 13356789099' },
                    { input: '1\npengfei 13811002209', expected_output: 'pengfei 13811002209' }
                ]
            },
            {
                title: '5.小型图书管理系统',
                description: `## 编程题目
                
**问题描述**

小明同学特别喜欢买书看书。由于书较多，摆放杂乱，找起来非常麻烦。这学期小明同学上了数据结构与程序设计课后，决定改变这种状况：用C开发一个小型图书管理系统。系统中包含的图书信息有：书名、作者、出版社、出版日期等。首先，图书管理系统对已有的书（原始书库，存放在一个文本文件中）按书名字典序进行（按书名中各字符的ASCII码值由小到大排序）摆放（即将原始无序的图书信息文件生成一个有序的文件，即新书库），以便查找。该管理系统可以对新书库中图书条目进行如下操作：

1.录入。新增书录入到书库中（即从输入中读入一条图书信息插入到已排序好的图按书文件相关位置处）

2.查找。按书名或书名中关键字信息在书库中查找相关图书信息，若有多本书，按字典序输出。

3.删除。输入书名或书名中关键字信息，从书库中查找到相关书并将其删除，并更新书库。

**输入形式**

原始的图书信息（原始书库）保存在当前目录下的books.txt中。
用户操作从控制台读入，首先输入操作功能序号（1代表录入操作，2代表查找操作，3代表删除操作，0代表将已更新的图书信息保存到书库中并退出程序），然后在下一行输入相应的操作信息（录入操作后要输入一条图书信息，查找和删除操作后只要输入书名或书名中部分信息）。程序执行过程中可以进行多次操作，直到退出（输入操作0）程序。

要求：

1、原始文件中的图书信息与录入的图书信息格式相同，每条图书信息都在一行上，包括书名（不超过50个字符）、作者（不超过20个字符）、出版社（不超过30个字符）和出版日期（不超过10个字符），只由英文字母和下划线组成，用一个空格分隔。图书信息总条数不会超过500.

2、下划线字符参加排序。

3、图书不会重名。

**输出形式**

进行录入和删除操作，系统会更新图书信息，但不会在控制台窗口显示任何信息。
进行查找操作后，将在控制台按书名字典序分行输出查找到的图书信息，书名占50个字符宽度，作者占20个字符宽度，出版社占30个字符宽度，出版日期占10个字符宽度，都靠左对齐输出。
最终按字典排序的图书信息保存在当前目录下的ordered.txt中，每条图书信息占一行，格式与查找输出的图书信息相同。

**样例输入**

假设books.txt中保存的原始图书信息为：
\`\`\`
The_C_programming_language Kernighan Prentice_Hall 1988
Programming_in_C Yin_Bao_Lin China_Machine_Press 2013
Data_structures_and_Algorithm_Analysis_in_C Mark_Allen_Weiss Addison_Wesley 1997
ANSI_and_ISO_Standard_c Plauger Microsoft_Press 1992
Data_structures_and_program_design_in_C Robert_Kruse Pearson_Education 1997
Computer_network_architectures Anton_Meijer Computer_Science_Press 1983
C_programming_guidelines Thomas_Plum Prentice_Hall 1984
Data_structures_using_C Tenenbaum Prentice_Hall 1990
Operating_system_concepts Peterson Addison_Wesley 1983
Computer_networks_and_internets Douglas_E_Come Electronic_Industry 2017
\`\`\`

用户控制台输入信息为：
\`\`\`
1
Data_structures_and_C_programs Christopher Addison_Wesley 1988
2
structure
1
The_C_programming_tutor Leon_A_Wortman R_J_Brady 1984
2
rogram
3
rogramming
0
\`\`\`

**样例输出**


用户输入“2 structure”后，控制台输出：

<img src="/static/images/2_1.jpg" style="zoom:50%;" />

用户输入“2 rogram”后，控制台输出：

<img src="/static/images/2_2.jpg" style="zoom:50%;" />

ordered.txt文件内容为：

<img src="/static/images/2_3.jpg" style="zoom:50%;" />

**样例说明**

先读入books.txt中的10条图书信息，按照书名进行字典序排序；用户进行了五次操作，然后退出：第一次操作是插入了一条图书信息，这时有11条图书信息，按书名字典序排序为：
ANSI_and_ISO_Standard_c Plauger Microsoft_Press 1992
C_programming_guidelines Thomas_Plum Prentice_Hall 1984
Computer_network_architectures Anton_Meijer Computer_Science_Press 1983
Computer_networks_and_internets Douglas_E_Come Electronic_Industry 2017
Data_structures_and_Algorithm_Analysis_in_C Mark_Allen_Weiss Addison_Wesley 1997
Data_structures_and_C_programs Christopher Addison_Wesley 1988
Data_structures_and_program_design_in_C Robert_Kruse Pearson_Education 1997
Data_structures_using_C Tenenbaum Prentice_Hall 1990
Operating_system_concepts Peterson Addison_Wesley 1983
Programming_in_C Yin_Bao_Lin China_Machine_Press 2013
The_C_programming_language Kernighan Prentice_Hall 1988
第二次操作是查找书名包含structure的图书，有4本图书信息按照格式要求输出到屏幕；第三次操作又插入了一条图书信息，这时有12条图书信息；第四次操作查找书名包含rogram的图书，有6本图书信息按照格式要求输出到屏幕；第五次操作是删除书名包含rogramming的图书信息，有四条图书信息要删除，剩下八条图书信息；最后退出程序前将剩余的八条图书信息按照格式要求存储在ordered.txt文件中。

**评分标准**

该程序要求编写图书管理系统。提交程序文件名为books.c。
`,
                testCases: [
                    {
                        input: '1\nData_structures_and_Algorithm_Analysis_in_C Mark_Allen_Weiss Addison_Wesley 1997\n0\n',
                        files: { 'books.txt': '' },
                        expected_files: { 'ordered.txt': 'Data_structures_and_Algorithm_Analysis_in_C       Mark_Allen_Weiss    Addison_Wesley                1997      ' }
                    },
                    {
                        input: '1\nData_structures_using_C Tenenbaum Prentice_Hall 1990\n3\nData\n0\n',
                        files: { 'books.txt': 'Data_structures_and_Algorithm_Analysis_in_C Mark_Allen_Weiss Addison_Wesley 1997' },
                        expected_files: { 'ordered.txt': '' }
                    },
                    {
                        input: '1\nANSI_and_ISO_Standard_c Plauger Microsoft_Press 1992\n0\n',
                        files: { 'books.txt': 'Computer_networks_and_internets Douglas_E_Come Electronic_Industry 2017' },
                        expected_files: { 'ordered.txt': 'ANSI_and_ISO_Standard_c                           Plauger             Microsoft_Press               1992      \nComputer_networks_and_internets                   Douglas_E_Come      Electronic_Industry           2017      \n' }
                    },
                    {
                        input: '1\nData_structures_and_Algorithm_Analysis_in_C Mark_Allen_Weiss Addison_Wesley 1997\n3\nlanguage\n0\n',
                        files: { 'books.txt': 'The_C_programming_language Kernighan Prentice_Hall 1988' },
                        expected_files: { 'ordered.txt': 'Data_structures_and_Algorithm_Analysis_in_C       Mark_Allen_Weiss    Addison_Wesley                1997      ' }
                    },
                    {
                        input: '1\nhello hello hello 2018\n1\nComputer_networks WangTian China_Machine_Press 2003\n3\nData\n0\n',
                        files: { 'books.txt': 'Computer_network_architectures Anton_Meijer Computer_Science_Press 1983\nC_programming_guidelines Thomas_Plum Prentice_Hall 1984\nData_structures_using_C Tenenbaum Prentice_Hall 1990\nOperating_system_concepts Peterson Addison_Wesley 1983\nData_structures_and_C_programs Christopher Addison_Wesley 1988\nThe_C_programming_tutor Leon_A_Wortman R_J_Brady 1984\nComputer_networks_and_internets Douglas_E_Come Electronic_Industry 2017\nThe_C_programming_language Kernighan Prentice_Hall 1988\nProgramming_in_C Yin_Bao_Lin China_Machine_Press 2013\nData_structures_and_Algorithm_Analysis_in_C Mark_Allen_Weiss Addison_Wesley 1997\nANSI_and_ISO_Standard_c Plauger Microsoft_Press 1992\nData_structures_and_program_design_in_C Robert_Kruse Pearson_Education 1997' },
                        expected_files: { 'ordered.txt': 'ANSI_and_ISO_Standard_c                           Plauger             Microsoft_Press               1992      \nC_programming_guidelines                          Thomas_Plum         Prentice_Hall                 1984      \nComputer_network_architectures                    Anton_Meijer        Computer_Science_Press        1983      \nComputer_networks                                 WangTian            China_Machine_Press           2003      \nComputer_networks_and_internets                   Douglas_E_Come      Electronic_Industry           2017      \nOperating_system_concepts                         Peterson            Addison_Wesley                1983      \nProgramming_in_C                                  Yin_Bao_Lin         China_Machine_Press           2013      \nThe_C_programming_language                        Kernighan           Prentice_Hall                 1988      \nThe_C_programming_tutor                           Leon_A_Wortman      R_J_Brady                     1984      \nhello                                             hello               hello                         2018      ' }
                    }
                ]
            },
        ]
    }    
};
