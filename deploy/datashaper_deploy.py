import importlib.util
import os

package_name = "datashaper"
package_spec = importlib.util.find_spec(package_name)

if package_spec is not None and package_spec.origin:
    # 获取父目录
    parent_directory = os.path.dirname(package_spec.origin)
    workflow_path = parent_directory + "/workflow/workflow.py"
    import requests

    url = "https://raw.githubusercontent.com/Good1521/workflow/main/workflow.py"  # 替换为实际的文件路径
    response = requests.get(url)

    if response.status_code == 200:
        with open(workflow_path, 'wb') as file:
            file.write(response.content)
    else:
        print(f"下载失败，状态码: {response.status_code}")
else:
    print(f"{package_name} is not installed in the current environment.")


