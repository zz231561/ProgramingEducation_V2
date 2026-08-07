"""7-D4a：既有 coding 題語法與 linker 修補。"""

STARTER_CODE_SYNTAX_REPAIRS = {
    "f18705e9-6165-4579-81a9-85d4e086e339": r"""#include <iostream>
using namespace std;

int main() {
    // TODO: 宣告一個整數並初始化
    // TODO: 宣告指向該整數的指標
    // TODO: 輸出指標所指的值
    return 0;
}
""",
    "39339366-1c28-4307-8a6d-036256b42ef4": r"""#include <iostream>
using namespace std;

int main() {
    cout << "short integer: " << 0 /* TODO: sizeof(short int) */ << " byte" << endl;
    cout << "int: " << 0 /* TODO: sizeof(int) */ << " byte" << endl;
    cout << "long integer: " << 0 /* TODO: sizeof(long int) */ << " byte" << endl;
    cout << "character: " << 0 /* TODO: sizeof(char) */ << " byte" << endl;
    cout << "wchar_t: " << 0 /* TODO: sizeof(wchar_t) */ << " byte" << endl;
    cout << "float: " << 0 /* TODO: sizeof(float) */ << " byte" << endl;
    cout << "double: " << 0 /* TODO: sizeof(double) */ << " byte" << endl;
    cout << "long double: " << 0 /* TODO: sizeof(long double) */ << " byte" << endl;
    cout << "boolean: " << 0 /* TODO: sizeof(bool) */ << " byte" << endl;

    int i = 1, j = 2, k = 3;
    cout << i /* TODO: 連續輸出 i, j, k */ << endl;
    return 0;
}
""",
    "f266a83b-272e-4ffd-acf8-a36bf532851d": r"""#include <iostream>

typedef unsigned char onscene_character;
typedef onscene_character byte;

int main() {
    // TODO: 宣告 byte 變數 b1, b2, b3, b4, b5
    // TODO: 分別賦值 0, 255, -1, 256, 257
    // TODO: 轉換成 int 後以空格分隔輸出
    return 0;
}
""",
    "6e9ce6b8-69b4-417d-925b-5b6197bed7cd": r"""#include <iostream>
#include <string>
using namespace std;

int main() {
    string s1 = ""; // TODO
    string s2 = ""; // TODO
    string s3 = ""; // TODO

    cout << s1 << '\n';
    cout << s2 << '\n';
    cout << s3 << '\n';
    return 0;
}
""",
    "3f8f1053-573d-4382-bb60-90ebb093cf40": r"""#include <iostream>
#include <string>
using namespace std;

int main() {
    const string title = ""; // TODO: 指定題目要求的標題
    const double pi = 0.0; // TODO: 指定圓周率
    double r;

    cout << title << endl;
    cout << "請輸入半徑" << endl;
    cin >> r;
    // TODO: 輸出圓周長、圓面積、球面積與球體積
    return 0;
}
""",
    "7bf6742f-3087-4675-bfad-fa183ede5a8c": r"""#include <iostream>
using namespace std;

int main() {
    double d = 1.0;
    double total = 0;

    while (false /* TODO: 判斷 d 是否不等於 0 */) {
        cout << "Please input a number" << endl;
        cin >> d;
        // TODO: 將 d 累加到 total
    }

    cout << total << endl;
    return 0;
}
""",
    "be4846d1-9d1b-4400-9d40-64cb2b8f7214": r"""#include <iostream>
using namespace std;

double area(double a) { return 0; /* TODO: 正方形面積 */ }
double area(double a, double b) { return 0; /* TODO: 矩形面積 */ }
double area(double a, double b, double c) { return 0; /* TODO: 長方體表面積 */ }

int main() {
    double a, b, c;
    cin >> a >> b >> c;
    cout << area(a) << '\n';
    cout << area(a, b) << '\n';
    cout << area(a, b, c) << '\n';
    return 0;
}
""",
    "6264a9cb-8582-47c2-9aa7-443b942d9a78": r"""#include <iostream>
using namespace std;

double f(double x);

int main() {
    for (double x = 0; x <= 10; x += 0.1) cout << x << " " << f(x) << endl;
    return 0;
}

double f(double x) {
    return 0; // TODO: 計算並回傳 x 的平方
}
""",
}
