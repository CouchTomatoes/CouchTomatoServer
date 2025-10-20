using AutoMapper;
using Serilog;
using CouchTomato.Data;
using CouchTomato.Core.Config;
using Microsoft.EntityFrameworkCore;
using CouchTomato.Core.Infrastructure;
using CouchTomato.Core.Interfaces;
using CouchTomato.Core.Mapping;
using CouchTomato.Core.Repositories;

var builder = WebApplication.CreateBuilder(args);

Log.Logger = new LoggerConfiguration()
    .Enrich.FromLogContext()
    .WriteTo.Console()
    .WriteTo.File("logs/couchtomato-.log", rollingInterval: RollingInterval.Day)
    .CreateLogger();

builder.Host.UseSerilog();

// --- Add services ---
builder.Services.Configure<AppSettings>(builder.Configuration.GetSection("AppSettings"));
builder.Services.AddSingleton<ConfigService>();
builder.Services.AddControllers();
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();

builder.Services.AddDbContext<CouchTomatoContext>(options =>
    options.UseSqlite(builder.Configuration.GetConnectionString("DefaultConnection")));

// Clean AutoMapper setup (no extra BuildServiceProvider)
builder.Services.AddSingleton<IMapper>(sp =>
{
    var loggerFactory = sp.GetRequiredService<ILoggerFactory>();

    var config = new MapperConfiguration(cfg =>
    {
        cfg.AddProfile<MappingProfile>();
    }, loggerFactory);

    return config.CreateMapper();
});

// Repositories & UoW
builder.Services.AddScoped(typeof(IEntityBaseRepository<>), typeof(EntityBaseRepository<>));
builder.Services.AddScoped<MovieRepository>();
builder.Services.AddScoped<IUnitOfWork, UnitOfWork>();

var app = builder.Build();

// Ensure data directory exists
CheckIfDbzdirectoryExistsAndCreate();

// Create DB if not exists
CreateDB();

app.UseSwagger();
app.UseSwaggerUI();

// Map controllers
app.MapControllers();

app.Run();

void CheckIfDbzdirectoryExistsAndCreate()
{
    var cfgService = app.Services.GetRequiredService<ConfigService>();
    var cfg = cfgService.Get();
    var dataPath = cfg.DataPath;
    
    // Determine base path (go one level up from API project to src/)
    var projectRoot = Directory.GetParent(Directory.GetCurrentDirectory())!.FullName;
    var dataDir = Path.Combine(projectRoot, cfg.DataPath);

    if (!Directory.Exists(dataDir))
    {
        Directory.CreateDirectory(dataDir);
        Console.WriteLine($"[Init] Created data directory at: {dataDir}");
    }
    else
    {
        Console.WriteLine($"[Init] Data directory already exists: {dataDir}");
    }
}

void CreateDB()
{
    using var scope = app.Services.CreateScope();
    var db = scope.ServiceProvider.GetRequiredService<CouchTomatoContext>();
    db.Database.EnsureCreated();
}
