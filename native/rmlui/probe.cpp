// CALYRA Stage A: genuine RmlUi 6.3 native OpenGL 3 window probe.
// This adapter has NOT been built or run in the current Linux sandbox.
// It uses the upstream GLFW_GL3 renderer, never Chromium or a WebView.
#include <RmlUi/Core.h>
#include <RmlUi/Core/Event.h>
#include <RmlUi/Core/EventListener.h>
#include <RmlUi_Backend.h>
#ifdef __APPLE__
#include <OpenGL/gl3.h>
#else
#include <GL/gl.h>
#endif
#include <chrono>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <iterator>
#include <memory>
#include <string>
#include <thread>
#include <vector>

namespace {
std::string ReadAll(const char* name) {
  std::ifstream f(name, std::ios::binary);
  if (!f) return {};
  return std::string(std::istreambuf_iterator<char>(f), std::istreambuf_iterator<char>());
}

class ApplyListener final : public Rml::EventListener {
public:
  ApplyListener(Rml::ElementDocument* d, bool& clicked) : doc_(d), clicked_(clicked) {}
  void ProcessEvent(Rml::Event&) override {
    clicked_ = true;
    if (Rml::Element* status = doc_->GetElementById("action-status")) {
      status->SetInnerRML("Native RmlUi click event received");
      std::cerr << "CALYRA_NATIVE_CLICK=1\n";
    }
  }
private:
  Rml::ElementDocument* doc_;
  bool& clicked_;
};

bool SaveBackbufferPPM(const std::string& path, int& width, int& height) {
  GLint viewport[4] = {0,0,0,0};
  glGetIntegerv(GL_VIEWPORT, viewport);
  width = viewport[2]; height = viewport[3];
  if (width <= 0 || height <= 0 || width > 8192 || height > 8192) return false;
  std::vector<unsigned char> rgba(size_t(width) * size_t(height) * 4);
  glFinish();
  glReadBuffer(GL_BACK);
  glReadPixels(0, 0, width, height, GL_RGBA, GL_UNSIGNED_BYTE, rgba.data());
  if (glGetError() != GL_NO_ERROR) return false;
  std::ofstream dst(path, std::ios::binary);
  if (!dst) return false;
  dst << "P6\n" << width << " " << height << "\n255\n";
  // OpenGL origin is bottom left; PPM's top row is first.
  for (int y = height - 1; y >= 0; --y) {
    for (int x = 0; x < width; ++x) {
      const size_t i = (size_t(y) * size_t(width) + size_t(x)) * 4;
      dst.write(reinterpret_cast<const char*>(&rgba[i]), 3);
    }
  }
  return dst.good();
}
} // namespace

int main(int argc, char** argv) {
  if (argc != 5) {
    std::cerr << "Usage: calyra_rmlui_probe <controls.rml> <css-file> <font.ttf> <out.ppm>\n";
    return 2;
  }
  std::string markup = ReadAll(argv[1]);
  const std::string css = ReadAll(argv[2]);
  if (markup.empty() || css.empty()) {
    std::cerr << "CALYRA_ERROR=missing_markup_or_css\n";
    return 3;
  }
  constexpr int width = 1060, height = 740;
  if (!Backend::Initialize("CALYRA / RmlUi 6.3", width, height, true)) {
    std::cerr << "CALYRA_ERROR=native_glfw_backend_init_failed\n";
    return 4;
  }
  Rml::SetSystemInterface(Backend::GetSystemInterface());
  Rml::SetRenderInterface(Backend::GetRenderInterface());
  Rml::Initialise();
  const char* gl_renderer = reinterpret_cast<const char*>(glGetString(GL_RENDERER));
  const char* gl_vendor = reinterpret_cast<const char*>(glGetString(GL_VENDOR));
  if (gl_renderer) std::cout << "CALYRA_GL_RENDERER=" << gl_renderer << "\n";
  if (gl_vendor) std::cout << "CALYRA_GL_VENDOR=" << gl_vendor << "\n";
  int result = 0;
  bool native_click_received = false;
  std::unique_ptr<ApplyListener> listener;  // Must outlive RmlUi document teardown.
  {
    if (!Rml::LoadFontFace(argv[3])) {
      std::cerr << "CALYRA_ERROR=font_load_failed\n";
      result = 5;
    } else if (Rml::Context* context = Rml::CreateContext("calyra", Rml::Vector2i(width, height))) {
      auto pos = markup.find("</head>");
      if (pos == std::string::npos) {
        std::cerr << "CALYRA_ERROR=invalid_rml_head\n";
        result = 6;
      } else {
        markup.insert(pos, "<style>\n" + css + "\n</style>\n");
        if (Rml::ElementDocument* document = context->LoadDocumentFromMemory(markup, "calyra-controls.rml")) {
          listener = std::make_unique<ApplyListener>(document, native_click_received);
          if (Rml::Element* apply = document->GetElementById("apply")) apply->AddEventListener("click", listener.get());
          else { std::cerr << "CALYRA_ERROR=button_missing\n"; result = 7; }
          if (result == 0) {
            document->Show();
            auto started = std::chrono::steady_clock::now();
            int frames = 0;
            bool captured = false;
            bool simulated_click_attempted = false;
            bool computed_style_recorded = false;
            while (std::chrono::steady_clock::now() - started < std::chrono::seconds(7)) {
              if (!Backend::ProcessEvents(context, nullptr, false)) break;
              context->Update();
              if (!computed_style_recorded) {
                if (Rml::Element* button = document->GetElementById("apply")) {
                  const auto color = button->GetComputedValues().background_color();
                  std::cout << "CALYRA_COMPUTED_PRIMARY_BG=" << int(color.red) << "," << int(color.green)
                            << "," << int(color.blue) << "," << int(color.alpha) << "\n";
                  computed_style_recorded = true;
                }
              }
              // Smoke-test RmlUi's own event dispatch via synthetic input. This
              // does NOT certify the operating-system keyboard/IME input path.
              if (!simulated_click_attempted && frames >= 3) {
                simulated_click_attempted = true;
                if (Rml::Element* button = document->GetElementById("apply")) {
                  const Rml::Vector2f pos = button->GetAbsoluteOffset(Rml::BoxArea::Border);
                  const int x = static_cast<int>(pos.x + button->GetOffsetWidth() * 0.5f);
                  const int y = static_cast<int>(pos.y + button->GetOffsetHeight() * 0.5f);
                  context->ProcessMouseMove(x, y, 0);
                  context->ProcessMouseButtonDown(0, 0);
                  context->ProcessMouseButtonUp(0, 0);
                  std::cout << "CALYRA_INPUT_SOURCE=synthetic_rmlui_event\n";
                }
              }
              Backend::BeginFrame();
              context->Render();
              if (!captured && frames >= 8) {
                int w=0, h=0;
                captured = SaveBackbufferPPM(argv[4], w, h);
                if (captured) std::cout << "CALYRA_NATIVE_FRAME=" << w << "x" << h << "\n";
                else std::cerr << "CALYRA_ERROR=gl_capture_failed\n";
              }
              Backend::PresentFrame();
              ++frames;
              std::this_thread::sleep_for(std::chrono::milliseconds(16));
            }
            if (!captured) result = 8;
            else if (!native_click_received) {
              std::cerr << "CALYRA_ERROR=synthetic_click_not_received\n";
              result = 11;
            }
          }
        } else { std::cerr << "CALYRA_ERROR=invalid_rml_document\n"; result = 9; }
      }
    } else { std::cerr << "CALYRA_ERROR=context_init_failed\n"; result = 10; }
  }
  Rml::Shutdown();  // Disposes documents and listeners before listener object dies.
  listener.reset();
  Backend::Shutdown();
  if (result == 0) std::cout << "CALYRA_NATIVE_RENDER_OK=1\n";
  return result;
}
