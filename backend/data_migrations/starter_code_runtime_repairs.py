"""7-D4a：runtime-safe starter code 修補。"""

STARTER_CODE_RUNTIME_REPAIRS = {
    "d226cdc3-38b4-4acc-aa11-878a8ec0aab2": r"""#include <iostream>
using namespace std;

int main() {
    int i = 10;
    int *i_ptr = nullptr;

    // TODO: 將 i 的地址設定給 i_ptr
    cout << i << endl;
    // TODO: 輸出 i_ptr 與其指向的內容，再透過 i_ptr 將內容改為 20
    cout << i << endl;
    if (i_ptr != nullptr) {
        cout << *i_ptr << endl;
    }
    return 0;
}
""",
    "95e40f2e-71ac-40a9-853f-4a3ff3216831": r"""#include <iostream>
using namespace std;

int add_to_static() {
    return 0; // TODO: 使用 static x，每次加 2 並回傳
}

int add_to_auto() {
    return 0; // TODO: 使用普通局部 x，每次加 2 並回傳
}

int main() {
    int x = 100;
    for (int i = 1; i <= 10; ++i) {
        int x = i;
        cout << x << "\n";
    }
    { int x = 200; cout << x << "\n"; }
    cout << x << "\n";
    for (int i = 1; i <= 5; ++i) cout << add_to_static() << "\n";
    for (int i = 1; i <= 5; ++i) cout << add_to_auto() << "\n";
    return 0;
}
""",
    "497cb57b-bf08-4376-9b21-6ff47fb6bb4e": r"""#include <iostream>
using namespace std;

int add_to_static() {
    return 0; // TODO: 使用 static x，每次加 2 並回傳
}

int add_to_auto() {
    return 0; // TODO: 使用普通局部 x，每次加 2 並回傳
}

int main() {
    int x = 100;
    for (int x = 1; x <= 10; x++) cout << x;
    cout << endl;
    { int x = 200; cout << x << endl; }
    cout << x << endl;
    for (int x = 1; x <= 5; x++) cout << add_to_static();
    cout << endl;
    for (int x = 1; x <= 5; x++) cout << add_to_auto();
    cout << endl;
    return 0;
}
""",
    "6028d0fa-5117-44be-86c0-79ab5066603d": r"""#include <iostream>
using namespace std;

int main() {
    int Score[100];
    int N = 1; // stdin 缺席時仍保持安全；TODO 完成後由輸入覆蓋
    int PASS = 0, STUN = 0, TOTAL = 0;

    cin >> N;
    // TODO: 輸入成績並統計 PASS、STUN、TOTAL
    cout << "及格人數: " << PASS << endl;
    cout << "不及格人數: " << STUN << endl;
    cout << "平均: " << TOTAL / N << endl;
    // TODO: 以相反順序輸出所有成績
    return 0;
}
""",
}
