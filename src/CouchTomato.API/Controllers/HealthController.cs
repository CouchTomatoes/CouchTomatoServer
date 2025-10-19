using Microsoft.AspNetCore.Mvc;
using CouchTomato.Core.Config;

namespace CouchTomato.API.Controllers;

[ApiController]
[Route("api/[controller]")]
public class HealthController : ControllerBase
{
    private readonly ConfigService _config;
    public HealthController(ConfigService config)
    {
        _config = config;
    }

    [HttpGet("status")]
    public IActionResult GetStatus()
    {
        var info = _config.Get();
        return Ok(new
        {
            status = "ok",
            app = info.ApplicationName,
            version = info.Version,
            time = DateTime.UtcNow
        });
    }
}
