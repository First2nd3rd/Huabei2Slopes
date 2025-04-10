from flask import Flask, render_template_string, request, send_file
import os
import tempfile
from converter_gpx import process_track, handle_duplicate_filenames

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>滑呗转 Slopes 转换器</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            text-align: center;
        }
        .url-input {
            width: 100%;
            padding: 10px;
            margin: 10px 0;
            border: 1px solid #ddd;
            border-radius: 4px;
        }
        .add-btn {
            background-color: #4CAF50;
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }
        .remove-btn {
            background-color: #f44336;
            color: white;
            padding: 5px 10px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            margin-left: 10px;
        }
        .submit-btn {
            background-color: #2196F3;
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            width: 100%;
            margin-top: 20px;
        }
        .url-list {
            margin: 20px 0;
        }
        .url-item {
            display: flex;
            align-items: center;
            margin: 10px 0;
        }
        .timezone-select {
            padding: 10px;
            margin: 10px 0;
            border: 1px solid #ddd;
            border-radius: 4px;
        }
        .message {
            margin: 20px 0;
            padding: 10px;
            border-radius: 4px;
        }
        .success {
            background-color: #dff0d8;
            color: #3c763d;
        }
        .error {
            background-color: #f2dede;
            color: #a94442;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>滑呗转 Slopes 转换器</h1>
        
        <form id="urlForm" method="post" enctype="multipart/form-data">
            <div id="urlList" class="url-list">
                <div class="url-item">
                    <input type="text" name="urls[]" class="url-input" placeholder="输入滑呗分享链接">
                    <button type="button" class="remove-btn" onclick="removeUrl(this)">删除</button>
                </div>
            </div>
            
            <button type="button" class="add-btn" onclick="addUrl()">添加更多链接</button>
            
            <select name="timezone" class="timezone-select">
                <option value="-12">UTC-12:00</option>
                <option value="-11">UTC-11:00</option>
                <option value="-10">UTC-10:00</option>
                <option value="-9">UTC-09:00</option>
                <option value="-8">UTC-08:00</option>
                <option value="-7">UTC-07:00</option>
                <option value="-6">UTC-06:00</option>
                <option value="-5">UTC-05:00</option>
                <option value="-4">UTC-04:00</option>
                <option value="-3">UTC-03:00</option>
                <option value="-2">UTC-02:00</option>
                <option value="-1">UTC-01:00</option>
                <option value="0" selected>UTC+00:00</option>
                <option value="1">UTC+01:00</option>
                <option value="2">UTC+02:00</option>
                <option value="3">UTC+03:00</option>
                <option value="4">UTC+04:00</option>
                <option value="5">UTC+05:00</option>
                <option value="6">UTC+06:00</option>
                <option value="7">UTC+07:00</option>
                <option value="8">UTC+08:00</option>
                <option value="9">UTC+09:00</option>
                <option value="10">UTC+10:00</option>
                <option value="11">UTC+11:00</option>
                <option value="12">UTC+12:00</option>
            </select>
            
            <button type="submit" class="submit-btn">转换并下载</button>
        </form>
    </div>

    <script>
        function addUrl() {
            const urlList = document.getElementById('urlList');
            const newUrlItem = document.createElement('div');
            newUrlItem.className = 'url-item';
            newUrlItem.innerHTML = `
                <input type="text" name="urls[]" class="url-input" placeholder="输入滑呗分享链接">
                <button type="button" class="remove-btn" onclick="removeUrl(this)">删除</button>
            `;
            urlList.appendChild(newUrlItem);
        }

        function removeUrl(button) {
            const urlList = document.getElementById('urlList');
            if (urlList.children.length > 1) {
                button.parentElement.remove();
            }
        }
    </script>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        urls = request.form.getlist('urls[]')
        timezone = int(request.form.get('timezone', 0))
        
        # Create a temporary directory for the output files
        with tempfile.TemporaryDirectory() as temp_dir:
            output_files = []
            processed_filenames = {}  # Track processed filenames to handle duplicates
            error_messages = []  # Track error messages
            
            for i, url in enumerate(urls, 1):
                if url.strip():  # Skip empty URLs
                    try:
                        print(f"Processing URL {i}: {url}")
                        output_file = process_track(url, timezone, temp_dir)
                        if output_file:
                            # Get the base filename without path
                            base_filename = os.path.basename(output_file)
                            print(f"Generated file: {base_filename}")
                            
                            # Handle duplicate filenames
                            if base_filename in processed_filenames:
                                processed_filenames[base_filename] += 1
                                # Format the number with leading zeros (e.g., 001, 002, etc.)
                                number = str(processed_filenames[base_filename]).zfill(3)
                                new_filename = f"{os.path.splitext(base_filename)[0]}_{number}.gpx"
                                new_path = os.path.join(temp_dir, new_filename)
                                print(f"Renaming duplicate file to: {new_filename}")
                                # Move the file to the new path instead of renaming
                                import shutil
                                shutil.move(output_file, new_path)
                                output_files.append((new_path, new_filename))
                            else:
                                processed_filenames[base_filename] = 1
                                # Format the first number with leading zeros
                                number = str(1).zfill(3)
                                new_filename = f"{os.path.splitext(base_filename)[0]}_{number}.gpx"
                                new_path = os.path.join(temp_dir, new_filename)
                                import shutil
                                shutil.move(output_file, new_path)
                                output_files.append((new_path, new_filename))
                        else:
                            error_messages.append(f"URL {i}: 无法生成文件")
                    except Exception as e:
                        error_msg = f"URL {i}: {str(e)}"
                        print(f"Error: {error_msg}")
                        error_messages.append(error_msg)
                        continue
            
            if output_files:
                print(f"Total files to be zipped: {len(output_files)}")
                # Create a zip file containing all GPX files
                import zipfile
                zip_path = os.path.join(temp_dir, 'converted_files.zip')
                with zipfile.ZipFile(zip_path, 'w') as zipf:
                    for file_path, file_name in output_files:
                        if os.path.exists(file_path):
                            print(f"Adding to zip: {file_name}")
                            zipf.write(file_path, file_name)
                        else:
                            print(f"Warning: File not found: {file_path}")
                
                if error_messages:
                    print("Errors occurred during processing:")
                    for msg in error_messages:
                        print(f"- {msg}")
                
                return send_file(
                    zip_path,
                    as_attachment=True,
                    download_name='converted_files.zip',
                    mimetype='application/zip'
                )
            else:
                error_message = "没有成功转换的文件"
                if error_messages:
                    error_message += "\n错误信息：\n" + "\n".join(error_messages)
                return render_template_string(HTML_TEMPLATE, message=error_message)
    
    return render_template_string(HTML_TEMPLATE)

if __name__ == '__main__':
    app.run(debug=True, port=5001) 