// 作业数据：每次作业包含多道题，每道题有题目描述和测试用例
// 此文件独立存放作业题目与测试点，方便维护和扩展
const HOMEWORK_DATA = {
    'homework1': {
        name: '第一次作业',
        problems: [
            {
                title: '可逆素数判断',
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
                title: '矩形相交面积',
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
                title: '求差集',
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
                title: '矩阵运算',
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
                title: '文件拷贝',
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
                title: '求两组整数的异或集',
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
                title: '凸多边形面积',
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
                title: '整数的N进制字符串表示',
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
                title: '最长升序子串（选做）',
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
                title: '合并字符串',
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
                title: '连续正整数的和',
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
                title: '合数分解',
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
                title: '计算公式：求π的值',
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
                title: '文件排版（非文件）',
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
                title: '注释比例',
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
                title: '删除子串',
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
    }
};
